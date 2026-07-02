# domains/biology.py
"""
Biology scenes:
  CellScene — animal cell, organelles revealed step-by-step with labels,
              gentle ambient motion (cytoplasm drift, membrane shimmer)
  DNAScene  — double helix, unzips and replicates with complementary bases
"""

import math
import time
import cv2
import numpy as np

from hud import (ACCENT, PURPLE, GREEN, AMBER, RED, TEXT, MUTED,
                 glass_panel, text, text_size, chip, FONT_S)
from . import Scene

MEMBRANE = (150, 180, 240)
CYTO     = (90, 140, 120)
NUCLEUS  = (200, 120, 180)
MITO     = (90, 110, 230)
GOLGI    = (60, 180, 220)


# ══════════════════════════════ cell ═══════════════════════════════
class CellScene(Scene):
    """Animal cell — each organelle is a labelled object revealed by steps."""

    ORGANELLES = {
        "membrane":     ("Cell Membrane", MEMBRANE),
        "cytoplasm":    ("Cytoplasm", CYTO),
        "nucleus":      ("Nucleus", NUCLEUS),
        "mitochondria": ("Mitochondria", MITO),
        "er":           ("Endoplasmic Reticulum", (120, 200, 160)),
        "golgi":        ("Golgi Apparatus", GOLGI),
        "ribosomes":    ("Ribosomes", AMBER),
    }

    def render(self, frame):
        cx, cy = int(self.W * 0.40), int(self.H * 0.55)
        rx, ry = 240, 200
        t = time.time()

        if "membrane" in self.visible:
            self._membrane(frame, cx, cy, rx, ry, t)
        if "cytoplasm" in self.visible:
            self._cytoplasm(frame, cx, cy, rx, ry)
        if "er" in self.visible:
            self._er(frame, cx, cy)
        if "golgi" in self.visible:
            self._golgi(frame, cx, cy)
        if "mitochondria" in self.visible:
            self._mitochondria(frame, cx, cy, t)
        if "ribosomes" in self.visible:
            self._ribosomes(frame, cx, cy, t)
        if "nucleus" in self.visible:
            self._nucleus(frame, cx, cy, t)

        self._legend(frame)
        return frame

    def _membrane(self, frame, cx, cy, rx, ry, t):
        overlay = frame.copy()
        cv2.ellipse(overlay, (cx, cy), (rx, ry), 0, 0, 360, CYTO, -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.18, frame, 0.82, 0, frame)
        # shimmering phospholipid bilayer
        shimmer = 0.6 + 0.4 * math.sin(t * 2)
        col = tuple(int(c * shimmer) for c in MEMBRANE)
        cv2.ellipse(frame, (cx, cy), (rx, ry), 0, 0, 360, col, 3, cv2.LINE_AA)
        cv2.ellipse(frame, (cx, cy), (rx - 7, ry - 7), 0, 0, 360, (100, 120, 170), 1, cv2.LINE_AA)

    def _cytoplasm(self, frame, cx, cy, rx, ry):
        # faint drifting particles
        t = time.time()
        rng = np.random.default_rng(3)
        for i in range(26):
            a = rng.uniform(0, 2 * math.pi)
            rr = rng.uniform(0.2, 0.85)
            px = int(cx + math.cos(a + t * 0.2) * rx * rr)
            py = int(cy + math.sin(a + t * 0.2) * ry * rr)
            cv2.circle(frame, (px, py), 2, (110, 160, 140), -1, cv2.LINE_AA)

    def _nucleus(self, frame, cx, cy, t):
        cv2.circle(frame, (cx, cy), 70, (150, 90, 140), -1, cv2.LINE_AA)
        overlay = frame.copy()
        cv2.circle(overlay, (cx, cy), 70, NUCLEUS, -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        cv2.circle(frame, (cx, cy), 70, (230, 180, 220), 2, cv2.LINE_AA)
        cv2.circle(frame, (cx + 18, cy - 12), 20, (140, 70, 120), -1, cv2.LINE_AA)  # nucleolus
        # chromatin specks
        rng = np.random.default_rng(11)
        for _ in range(14):
            px = cx + int(rng.uniform(-55, 55))
            py = cy + int(rng.uniform(-55, 55))
            if (px - cx) ** 2 / 70**2 + (py - cy) ** 2 / 70**2 < 1:
                cv2.circle(frame, (px, py), 2, (110, 50, 100), -1, cv2.LINE_AA)
        self._label(frame, cx, cy - 78, "Nucleus", NUCLEUS)

    def _mitochondria(self, frame, cx, cy, t):
        spots = [(-140, 70), (120, -90), (150, 90)]
        for i, (dx, dy) in enumerate(spots):
            mx, my = cx + dx, cy + dy
            ang = 20 * i + 10 * math.sin(t + i)
            cv2.ellipse(frame, (mx, my), (34, 17), ang, 0, 360, MITO, -1, cv2.LINE_AA)
            cv2.ellipse(frame, (mx, my), (34, 17), ang, 0, 360, (180, 190, 255), 1, cv2.LINE_AA)
            # cristae
            for k in range(-2, 3):
                x1 = int(mx + math.cos(math.radians(ang)) * k * 9)
                y1 = int(my + math.sin(math.radians(ang)) * k * 9)
                cv2.line(frame, (x1 - 6, y1 - 6), (x1 + 6, y1 + 6), (200, 205, 255), 1, cv2.LINE_AA)
        self._label(frame, cx - 140, cy + 96, "Mitochondria", MITO)

    def _er(self, frame, cx, cy):
        col = (120, 200, 160)
        for k in range(3):
            pts = []
            for a in range(0, 200, 12):
                r = 105 + k * 14 + 8 * math.sin(math.radians(a * 3))
                pts.append((int(cx + math.cos(math.radians(a - 40)) * r),
                            int(cy + math.sin(math.radians(a - 40)) * r * 0.8)))
            cv2.polylines(frame, [np.array(pts, np.int32)], False, col, 1, cv2.LINE_AA)

    def _golgi(self, frame, cx, cy):
        gx, gy = cx - 120, cy - 90
        for k in range(4):
            cv2.ellipse(frame, (gx, gy + k * 9), (34 - k * 4, 10), 15, 0, 180,
                        GOLGI, 2, cv2.LINE_AA)
        self._label(frame, gx - 20, gy - 16, "Golgi", GOLGI)

    def _ribosomes(self, frame, cx, cy, t):
        rng = np.random.default_rng(5)
        for _ in range(30):
            a = rng.uniform(0, 2 * math.pi)
            rr = rng.uniform(0.45, 0.9)
            px = int(cx + math.cos(a) * 230 * rr)
            py = int(cy + math.sin(a) * 190 * rr)
            cv2.circle(frame, (px, py), 3, AMBER, -1, cv2.LINE_AA)

    def _label(self, frame, x, y, s, col):
        tw, _ = text_size(s, 0.42, 1, FONT_S)
        chip(frame, s, x - tw // 2, y, col, 0.4)

    def _legend(self, frame):
        shown = [k for k in self.ORGANELLES if k in self.visible]
        if not shown:
            return
        x0, y0 = self.W - 264, 92
        h = 52 + 28 * len(shown)
        glass_panel(frame, x0, y0, 248, h, radius=16, border=PURPLE)
        text(frame, "CELL ORGANELLES", x0 + 16, y0 + 28, 0.5, PURPLE, 1, FONT_S)
        cv2.line(frame, (x0 + 16, y0 + 38), (x0 + 232, y0 + 38), (70, 60, 45), 1)
        for i, k in enumerate(shown):
            name, col = self.ORGANELLES[k]
            yy = y0 + 60 + i * 28
            cv2.circle(frame, (x0 + 24, yy - 4), 6, col, -1, cv2.LINE_AA)
            text(frame, name, x0 + 40, yy, 0.44, TEXT, 1, FONT_S)


# ══════════════════════════════ DNA ════════════════════════════════
class DNAScene(Scene):
    """Double helix that unzips and replicates. Bases colour-coded A-T, G-C."""

    BASE_COLORS = {"A": (80, 200, 120), "T": (80, 120, 240),
                   "G": (240, 180, 60), "C": (200, 100, 200)}
    COMPLEMENT = {"A": "T", "T": "A", "G": "C", "C": "G"}

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        rng = np.random.default_rng(21)
        self.seq = [list("ATGCTAGCTAGCATCG")[i] for i in range(16)]

    def render(self, frame):
        cx = int(self.W * 0.40)
        top, bot = int(self.H * 0.24), int(self.H * 0.84)
        n = len(self.seq)
        t = time.time()
        unzip = "unzip" in self.animations
        replicate = "replicate" in self.animations
        prog = min(self.elapsed() / 6.0, 1.0) if (unzip or replicate) else 0.0
        split_upto = int(n * prog)
        amp = 58

        for i in range(n):
            y = int(top + (bot - top) * i / (n - 1))
            phase = i * 0.45 + t * 1.2
            split = i < split_upto
            gap = 42 if split else 0
            lx = int(cx - amp * math.cos(phase) - gap)
            rx = int(cx + amp * math.cos(phase) + gap)

            base = self.seq[i]
            comp = self.COMPLEMENT[base]
            if not split:
                cv2.line(frame, (lx, y), (rx, y), (90, 100, 120), 2, cv2.LINE_AA)
                mid = (lx + rx) // 2
                cv2.circle(frame, (mid - 14, y), 6, self.BASE_COLORS[base], -1, cv2.LINE_AA)
                cv2.circle(frame, (mid + 14, y), 6, self.BASE_COLORS[comp], -1, cv2.LINE_AA)
            else:
                cv2.circle(frame, (lx + 20, y), 6, self.BASE_COLORS[base], -1, cv2.LINE_AA)
                cv2.circle(frame, (lx + 38, y), 6, self.BASE_COLORS[comp], -1, cv2.LINE_AA)
                cv2.circle(frame, (rx - 20, y), 6, self.BASE_COLORS[comp], -1, cv2.LINE_AA)
                cv2.circle(frame, (rx - 38, y), 6, self.BASE_COLORS[base], -1, cv2.LINE_AA)
            # backbone nodes on top
            cv2.circle(frame, (lx, y), 7, (205, 205, 215), -1, cv2.LINE_AA)
            cv2.circle(frame, (rx, y), 7, (205, 205, 215), -1, cv2.LINE_AA)

        # backbone strands (drawn thick, over bases)
        for sgn, gapf in ((-1, -1), (1, 1)):
            pts = []
            for i in range(n):
                y = int(top + (bot - top) * i / (n - 1))
                phase = i * 0.45 + t * 1.2
                gap = 42 if i < split_upto else 0
                x = int(cx + sgn * amp * math.cos(phase) + gapf * gap)
                pts.append((x, y))
            cv2.polylines(frame, [np.array(pts, np.int32)], False,
                          (170, 180, 200), 3, cv2.LINE_AA)

        if unzip and 0 < split_upto < n:
            fork_y = int(top + (bot - top) * split_upto / (n - 1))
            chip(frame, "REPLICATION FORK", cx - 66, fork_y - 4, ACCENT, 0.4)

        self._legend(frame, prog, split_upto, n)
        return frame

    def _legend(self, frame, prog, done, n):
        x0, y0 = self.W - 264, 92
        rows = [("BASE PAIRS", f"{n}", TEXT),
                ("UNZIPPED", f"{done}/{n}", ACCENT),
                ("PROGRESS", f"{prog*100:.0f}%", GREEN)]
        glass_panel(frame, x0, y0, 248, 130 + 24 * 4, radius=16, border=PURPLE)
        text(frame, "DNA REPLICATION", x0 + 16, y0 + 28, 0.5, PURPLE, 1, FONT_S)
        cv2.line(frame, (x0 + 16, y0 + 38), (x0 + 232, y0 + 38), (70, 60, 45), 1)
        for i, (k, v, col) in enumerate(rows):
            yy = y0 + 62 + i * 28
            text(frame, k, x0 + 16, yy, 0.44, MUTED, 1, FONT_S)
            vw, _ = text_size(v, 0.48, 1, FONT_S)
            text(frame, v, x0 + 232 - vw, yy, 0.48, col, 1, FONT_S)
        yy = y0 + 62 + 3 * 28 + 8
        text(frame, "BASE PAIRING", x0 + 16, yy, 0.42, TEXT, 1, FONT_S)
        for i, (b, c) in enumerate([("A", "T"), ("G", "C")]):
            ly = yy + 24 + i * 24
            cv2.circle(frame, (x0 + 26, ly - 4), 5, self.BASE_COLORS[b], -1, cv2.LINE_AA)
            cv2.circle(frame, (x0 + 46, ly - 4), 5, self.BASE_COLORS[c], -1, cv2.LINE_AA)
            text(frame, f"{b} = {c}", x0 + 60, ly, 0.42, TEXT, 1, FONT_S)
