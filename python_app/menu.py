# python_app/menu.py
"""
CircuitVerse v2 — interactive experiment menu.

A collapsible glass panel anchored top-left under the brand bar.
Collapsed  → a single "☰ EXPERIMENTS" button.
Expanded   → domain list; selecting a domain reveals its experiments.

Supports mouse (hover + click) and keyboard (↑/↓ + Enter, ←/Esc back,
number keys as shortcuts). The menu owns *no* experiment logic — it just
emits the chosen marker id / experiment file back to the app.
"""

import time
import cv2

from hud import (ACCENT, PURPLE, GREEN, AMBER, RED, TEXT, MUTED,
                 glass_panel, text, text_size, chip, FONT_S)

# domain palette
DOMAIN_META = {
    "Physics":   {"color": (11, 158, 245),  "icon": "P", "key": "physics"},
    "Chemistry": {"color": (180, 105, 255),  "icon": "C", "key": "chemistry"},
    "Biology":   {"color": (200, 120, 180),  "icon": "B", "key": "biology"},
}


class MenuItem:
    __slots__ = ("label", "marker", "sub", "rect")

    def __init__(self, label, marker=None, sub=None):
        self.label = label
        self.marker = marker        # experiment marker id (leaf) or None
        self.sub = sub              # domain key (branch) or None
        self.rect = (0, 0, 0, 0)    # x, y, w, h — filled at draw time


class ExperimentMenu:
    """
    Build once from the experiment catalog:
        catalog = {"Physics": [(marker_id, name), ...], ...}
    """

    BTN = (24, 90, 210, 44)        # collapsed button rect (x, y, w, h)
    PANEL_W = 340
    ROW_H = 46

    def __init__(self, catalog):
        self.catalog = catalog
        self.expanded = False
        self.active_domain = None       # None → showing domain list
        self.hover = None               # (kind, key)  kind in {"domain","exp","back"}
        self.sel_index = 0              # keyboard cursor
        self.mouse = (0, 0)
        self._domain_rects = []
        self._exp_rects = []
        self._back_rect = (0, 0, 0, 0)
        self._btn_rect = self.BTN
        self.on_pick = None             # callback(marker_id)

    # ─────────────────────────── input ────────────────────────────
    def handle_mouse(self, event, x, y, flags, param):
        self.mouse = (x, y)
        if event == cv2.EVENT_LBUTTONDOWN:
            self.click(x, y)

    def _in(self, rect, x, y):
        rx, ry, rw, rh = rect
        return rx <= x <= rx + rw and ry <= y <= ry + rh

    def click(self, x, y):
        # collapsed button
        if not self.expanded:
            if self._in(self._btn_rect, x, y):
                self.expanded = True
            return
        # toggle button (same spot, now "close")
        if self._in(self._btn_rect, x, y):
            self.expanded = False
            self.active_domain = None
            return
        if self.active_domain is None:
            for rect, key in self._domain_rects:
                if self._in(rect, x, y):
                    self.active_domain = key
                    self.sel_index = 0
                    return
        else:
            if self._in(self._back_rect, x, y):
                self.active_domain = None
                self.sel_index = 0
                return
            for rect, marker in self._exp_rects:
                if self._in(rect, x, y):
                    self._pick(marker)
                    return

    def handle_key(self, key):
        """Return True if the key was consumed by the menu."""
        if key == ord("m"):
            self.expanded = not self.expanded
            self.active_domain = None
            return True
        if not self.expanded:
            return False

        if key == 27:  # Esc
            if self.active_domain is not None:
                self.active_domain = None
            else:
                self.expanded = False
            return True
        if key in (81, 2, ord("h")):  # ← back
            if self.active_domain is not None:
                self.active_domain = None
                return True
        if key in (82, 0):            # ↑
            self.sel_index = max(0, self.sel_index - 1)
            return True
        if key in (84, 1):            # ↓
            self.sel_index = min(self._count() - 1, self.sel_index + 1)
            return True
        if key in (13, 10):           # Enter
            self._activate_selection()
            return True
        if ord("1") <= key <= ord("9"):
            idx = key - ord("1")
            if self.active_domain is None:
                domains = list(self.catalog.keys())
                if idx < len(domains):
                    self.active_domain = list(DOMAIN_META.keys())[idx] \
                        if idx < len(DOMAIN_META) else None
                    self.sel_index = 0
            else:
                exps = self.catalog.get(self.active_domain, [])
                if idx < len(exps):
                    self._pick(exps[idx][0])
            return True
        return False

    def _count(self):
        if self.active_domain is None:
            return len(self.catalog)
        return len(self.catalog.get(self.active_domain, []))

    def _activate_selection(self):
        if self.active_domain is None:
            domains = list(self.catalog.keys())
            if 0 <= self.sel_index < len(domains):
                self.active_domain = domains[self.sel_index]
                self.sel_index = 0
        else:
            exps = self.catalog.get(self.active_domain, [])
            if 0 <= self.sel_index < len(exps):
                self._pick(exps[self.sel_index][0])

    def _pick(self, marker):
        if self.on_pick:
            self.on_pick(marker)
        self.expanded = False
        self.active_domain = None

    # ─────────────────────────── drawing ──────────────────────────
    def draw(self, frame):
        mx, my = self.mouse
        if not self.expanded:
            self._draw_button(frame, "MENU  ·  EXPERIMENTS", mx, my, closed=True)
            return

        self._draw_button(frame, "CLOSE  ✕", mx, my, closed=False)
        if self.active_domain is None:
            self._draw_domains(frame, mx, my)
        else:
            self._draw_experiments(frame, mx, my)

    def _draw_button(self, frame, label, mx, my, closed):
        x, y, w, h = self.BTN
        self._btn_rect = self.BTN
        hovered = self._in(self._btn_rect, mx, my)
        col = ACCENT if closed else RED
        glass_panel(frame, x, y, w, h, radius=12,
                    border=col, border_alpha=0.8 if hovered else 0.4,
                    tint_strength=0.6 if hovered else 0.5)
        # hamburger / x icon
        ix = x + 18
        if closed:
            for k in range(3):
                cv2.line(frame, (ix, y + 15 + k * 7), (ix + 16, y + 15 + k * 7),
                         col, 2, cv2.LINE_AA)
        else:
            cv2.line(frame, (ix, y + 15), (ix + 16, y + 31), col, 2, cv2.LINE_AA)
            cv2.line(frame, (ix + 16, y + 15), (ix, y + 31), col, 2, cv2.LINE_AA)
        text(frame, label, x + 44, y + 28, 0.48, TEXT, 1, FONT_S)

    def _draw_domains(self, frame, mx, my):
        x = self.BTN[0]
        y0 = self.BTN[1] + self.BTN[3] + 10
        rows = list(self.catalog.keys())
        h = 44 + len(rows) * self.ROW_H
        glass_panel(frame, x, y0, self.PANEL_W, h, radius=16, border=ACCENT)
        text(frame, "SELECT A SUBJECT", x + 18, y0 + 28, 0.5, ACCENT, 1, FONT_S)
        cv2.line(frame, (x + 18, y0 + 38), (x + self.PANEL_W - 18, y0 + 38),
                 (70, 60, 45), 1)

        self._domain_rects = []
        for i, name in enumerate(rows):
            meta = DOMAIN_META.get(name, {"color": ACCENT, "icon": "?"})
            ry = y0 + 50 + i * self.ROW_H
            rect = (x + 12, ry, self.PANEL_W - 24, self.ROW_H - 8)
            self._domain_rects.append((rect, name))
            hovered = self._in(rect, mx, my) or (self.sel_index == i)
            self._row(frame, rect, meta["color"], meta["icon"], name,
                      f"{len(self.catalog[name])} experiments", hovered, i + 1)

    def _draw_experiments(self, frame, mx, my):
        x = self.BTN[0]
        y0 = self.BTN[1] + self.BTN[3] + 10
        exps = self.catalog.get(self.active_domain, [])
        meta = DOMAIN_META.get(self.active_domain, {"color": ACCENT})
        col = meta["color"]
        h = 92 + len(exps) * self.ROW_H
        glass_panel(frame, x, y0, self.PANEL_W, h, radius=16, border=col)

        # back row
        self._back_rect = (x + 12, y0 + 10, self.PANEL_W - 24, 32)
        back_hov = self._in(self._back_rect, mx, my)
        text(frame, "‹  BACK", x + 22, y0 + 32, 0.5,
             col if back_hov else MUTED, 1, FONT_S)
        chip(frame, self.active_domain.upper(), x + 120, y0 + 12, col, 0.42)
        cv2.line(frame, (x + 18, y0 + 50), (x + self.PANEL_W - 18, y0 + 50),
                 (70, 60, 45), 1)

        self._exp_rects = []
        for i, (marker, name) in enumerate(exps):
            ry = y0 + 60 + i * self.ROW_H
            rect = (x + 12, ry, self.PANEL_W - 24, self.ROW_H - 8)
            self._exp_rects.append((rect, marker))
            hovered = self._in(rect, mx, my) or (self.sel_index == i)
            short = name if len(name) < 34 else name[:31] + "…"
            self._row(frame, rect, col, str(i + 1), short,
                      f"marker {marker}", hovered, i + 1, small=True)

    def _row(self, frame, rect, col, icon, title, sub, hovered, num, small=False):
        rx, ry, rw, rh = rect
        if hovered:
            glass_panel(frame, rx, ry, rw, rh, radius=10,
                        border=col, border_alpha=0.9,
                        tint=(40, 30, 15), tint_strength=0.5, blur=7)
        # icon badge
        cv2.circle(frame, (rx + 20, ry + rh // 2), 13, col, 2, cv2.LINE_AA)
        tw, _ = text_size(icon, 0.5, 1, FONT_S)
        text(frame, icon, rx + 20 - tw // 2, ry + rh // 2 + 6, 0.5, col, 1, FONT_S)
        # title + sub
        text(frame, title, rx + 44, ry + (rh // 2) - 1 if sub else ry + rh // 2 + 5,
             0.5 if not small else 0.46, TEXT if hovered else (210, 205, 200),
             1, FONT_S)
        if sub:
            text(frame, sub, rx + 44, ry + rh - 8, 0.38, MUTED, 1, FONT_S, shadow=False)
        # keyboard number hint on the right
        text(frame, str(num), rx + rw - 22, ry + rh // 2 + 5, 0.42,
             col if hovered else MUTED, 1, FONT_S, shadow=False)
