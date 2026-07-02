# domains/chemistry.py
"""
Chemistry scenes:
  TitrationScene    — strong acid vs strong base, live pH curve,
                      phenolphthalein colour change at equivalence
  ElectrolysisScene — water splitting, animated bubbles, 2:1 H2:O2 volumes
"""

import math
import time
import cv2
import numpy as np

from hud import (ACCENT, PURPLE, GREEN, AMBER, RED, TEXT, MUTED,
                 glass_panel, text, text_size, chip, FONT_S)
from . import Scene

PINK = (180, 105, 255)


# ══════════════════════════════ titration ══════════════════════════
class TitrationScene(Scene):
    """
    pH of strong-acid/strong-base titration:
      before eq : [H+] = (CaVa − CbVb)/(Va+Vb)
      at eq     : pH 7
      after eq  : pOH from excess OH−
    Burette drips at DRIP_RATE mL/s while the 'titrate' animation runs.
    """
    DRIP_RATE = 1.6  # mL of base per second

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.Ca = self.sim.get("acid", {}).get("concentration", 0.1)
        self.Va = self.sim.get("acid", {}).get("volume_ml", 25.0)
        self.Cb = self.sim.get("base", {}).get("concentration", 0.1)
        self.acid_name = self.sim.get("acid", {}).get("name", "HCl")
        self.base_name = self.sim.get("base", {}).get("name", "NaOH")
        self.v_eq = self.Ca * self.Va / self.Cb
        self.v_max = self.v_eq * 2.0

    # ── model ──
    def ph_at(self, vb):
        Ca, Va, Cb = self.Ca, self.Va, self.Cb
        total = Va + vb
        na, nb = Ca * Va, Cb * vb
        if abs(na - nb) < 1e-9:
            return 7.0
        if nb < na:
            h = (na - nb) / total / 1000 * 1000  # mol/L (volumes in mL cancel)
            return max(-math.log10(max((na - nb) / total, 1e-14)), 0)
        return min(14 + math.log10(max((nb - na) / total, 1e-14)), 14)

    def vb_now(self):
        if "titrate" not in self.animations:
            return 0.0
        return min(self.elapsed() * self.DRIP_RATE, self.v_max)

    # ── render ──
    def render(self, frame):
        cx = int(self.W * 0.38)
        base_y = int(self.H * 0.88)      # flask sits low
        vb = self.vb_now()
        ph = self.ph_at(vb)
        past_eq = ph >= 8.2         # phenolphthalein endpoint

        if "stand" in self.visible:
            self._stand(frame, cx, base_y)
        if "flask" in self.visible:
            self._flask(frame, cx, base_y, ph, past_eq)
        if "burette" in self.visible:
            self._burette(frame, cx, base_y, vb,
                          dripping="titrate" in self.animations and vb < self.v_max)
        if "indicator" in self.visible:
            chip(frame, "PHENOLPHTHALEIN ADDED", cx - 100, base_y + 20, PINK, 0.4)

        if "titrate" in self.animations:
            self._ph_curve(frame, vb, ph)
            self._readout(frame, vb, ph, past_eq)
        return frame

    # ── drawing pieces ──
    def _stand(self, frame, cx, base_y):
        col = (140, 140, 150)
        rod_x = cx + 190
        cv2.line(frame, (cx - 60, base_y + 16), (rod_x + 20, base_y + 16), col, 6, cv2.LINE_AA)
        cv2.line(frame, (rod_x, base_y + 14), (rod_x, base_y - 430), col, 5, cv2.LINE_AA)
        # clamp arm reaching to the burette
        cv2.line(frame, (rod_x, base_y - 360), (cx + 16, base_y - 360), col, 4, cv2.LINE_AA)

    def _flask(self, frame, cx, base_y, ph, pink):
        neck_w, body_w, h = 22, 78, 120
        top = base_y - h
        pts = np.array([(cx - neck_w, top), (cx + neck_w, top),
                        (cx + neck_w, top + 32), (cx + body_w, base_y),
                        (cx - body_w, base_y)], np.int32)
        liquid = frame.copy()
        lig_col = PINK if pink else (235, 225, 215)
        lp = np.array([(cx - neck_w - 14, top + 54), (cx + neck_w + 14, top + 54),
                       (cx + body_w - 6, base_y - 5), (cx - body_w + 6, base_y - 5)], np.int32)
        cv2.fillPoly(liquid, [lp], lig_col)
        cv2.addWeighted(liquid, 0.45 if pink else 0.22, frame, 0.55 if pink else 0.78, 0, frame)
        cv2.polylines(frame, [pts], True, (230, 230, 235), 3, cv2.LINE_AA)
        if pink:
            t = time.time()
            for k in range(3):
                ang = t * 2 + k * 2.1
                ex = cx + int(30 * math.cos(ang))
                ey = base_y - 44 + int(12 * math.sin(ang * 1.3))
                cv2.circle(frame, (ex, ey), 8 + 3 * k, PINK, 1, cv2.LINE_AA)
        label = f"{self.acid_name}  {self.Va:.0f} mL"
        tw, _ = text_size(label, 0.46, 1, FONT_S)
        text(frame, label, cx - tw // 2, base_y + 40, 0.46, TEXT, 1, FONT_S)

    def _burette(self, frame, cx, base_y, vb, dripping):
        bx = cx
        top, bot = base_y - 420, base_y - 180   # tip well above flask mouth
        cv2.rectangle(frame, (bx - 11, top), (bx + 11, bot), (230, 230, 235), 2, cv2.LINE_AA)
        frac_empty = min(vb / self.v_max, 1.0)
        lvl = int(top + 6 + (bot - top - 34) * frac_empty)
        fill = frame.copy()
        cv2.rectangle(fill, (bx - 9, lvl), (bx + 9, bot - 22), ACCENT, -1)
        cv2.addWeighted(fill, 0.35, frame, 0.65, 0, frame)
        # graduation ticks
        for k in range(1, 8):
            ty = top + int((bot - top) * k / 8)
            cv2.line(frame, (bx + 11, ty), (bx + 17, ty), (180, 180, 190), 1, cv2.LINE_AA)
        # stopcock + tip
        cv2.rectangle(frame, (bx - 14, bot - 20), (bx + 14, bot - 6),
                      (150, 150, 160), -1, cv2.LINE_AA)
        cv2.line(frame, (bx, bot - 6), (bx, bot + 14), (230, 230, 235), 2, cv2.LINE_AA)
        if dripping:
            u = (time.time() * 2.2) % 1.0
            dy = int(bot + 16 + u * (base_y - 150 - bot))
            cv2.circle(frame, (bx, dy), 4, ACCENT, -1, cv2.LINE_AA)
        text(frame, f"{self.base_name} {self.Cb:.1f} M", bx + 22, top + 20, 0.44, ACCENT, 1, FONT_S)

    def _ph_curve(self, frame, vb, ph):
        x0, y0, w, h = self.W - 342, self.H - 250, 322, 205
        glass_panel(frame, x0, y0, w, h, radius=14, border=PURPLE)
        text(frame, "pH vs VOLUME OF BASE", x0 + 14, y0 + 24, 0.45, PURPLE, 1, FONT_S)
        gx, gy, gw, gh = x0 + 42, y0 + 38, w - 60, h - 66
        cv2.line(frame, (gx, gy), (gx, gy + gh), MUTED, 1, cv2.LINE_AA)
        cv2.line(frame, (gx, gy + gh), (gx + gw, gy + gh), MUTED, 1, cv2.LINE_AA)
        text(frame, "14", x0 + 14, gy + 10, 0.38, MUTED, 1, FONT_S, shadow=False)
        text(frame, "7", x0 + 20, gy + gh // 2 + 4, 0.38, MUTED, 1, FONT_S, shadow=False)
        text(frame, f"{self.v_max:.0f} mL", gx + gw - 34, gy + gh + 16, 0.38, MUTED, 1, FONT_S, shadow=False)
        # equivalence guide
        ex = gx + int(gw * self.v_eq / self.v_max)
        for yy in range(gy, gy + gh, 8):
            cv2.line(frame, (ex, yy), (ex, yy + 3), (90, 70, 130), 1)
        # curve up to current volume
        pts = []
        steps = 240
        for i in range(int(steps * vb / self.v_max) + 1):
            v = self.v_max * i / steps
            p = self.ph_at(v)
            pts.append((gx + int(gw * v / self.v_max),
                        gy + gh - int(gh * p / 14)))
        if len(pts) > 1:
            cv2.polylines(frame, [np.array(pts, np.int32)], False, PURPLE, 2, cv2.LINE_AA)
        if pts:
            cv2.circle(frame, pts[-1], 5, ACCENT, -1, cv2.LINE_AA)
            cv2.circle(frame, pts[-1], 9, ACCENT, 1, cv2.LINE_AA)

    def _readout(self, frame, vb, ph, past_eq):
        x0, y0 = self.W - 264, 92
        rows = [
            ("BASE ADDED", f"{vb:.1f} mL", ACCENT),
            ("pH", f"{ph:.2f}", PINK if past_eq else GREEN),
            ("EQUIV. PT", f"{self.v_eq:.1f} mL", PURPLE),
            ("INDICATOR", "PINK" if past_eq else "COLORLESS", PINK if past_eq else MUTED),
        ]
        ph_panel_h = 58 + 30 * len(rows)
        glass_panel(frame, x0, y0, 248, ph_panel_h, radius=16, border=ACCENT)
        text(frame, "LIVE TITRATION", x0 + 16, y0 + 28, 0.5, ACCENT, 1, FONT_S)
        cv2.line(frame, (x0 + 16, y0 + 38), (x0 + 232, y0 + 38), (70, 60, 45), 1)
        for i, (k, v, col) in enumerate(rows):
            yy = y0 + 64 + i * 30
            text(frame, k, x0 + 16, yy, 0.44, MUTED, 1, FONT_S)
            vw, _ = text_size(v, 0.48, 1, FONT_S)
            text(frame, v, x0 + 232 - vw, yy, 0.48, col, 1, FONT_S)


# ═════════════════════════════ electrolysis ════════════════════════
class ElectrolysisScene(Scene):
    """Water electrolysis — bubbles at both electrodes, H2:O2 = 2:1."""
    RATE_ML_S = 0.9  # O2 mL per second (H2 = 2×)

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.rng = np.random.default_rng(7)
        self.bubbles = []   # (x, y, r, speed, side)

    def render(self, frame):
        cx = int(self.W * 0.42)
        base_y = int(self.H * 0.80)
        running = "electrolyse" in self.animations
        t = self.elapsed()
        o2 = min(t * self.RATE_ML_S, 40) if running else 0.0
        h2 = 2 * o2

        if "cell" in self.visible:
            self._tank(frame, cx, base_y)
        if "electrodes" in self.visible:
            self._electrodes(frame, cx, base_y, running)
        if "battery" in self.visible:
            self._battery(frame, cx, base_y, running)
        if running:
            self._bubbles(frame, cx, base_y)
            self._tubes(frame, cx, base_y, h2, o2)
            self._readout(frame, h2, o2, t)
        return frame

    def _tank(self, frame, cx, y):
        w, h = 210, 190
        liquid = frame.copy()
        cv2.rectangle(liquid, (cx - w, y - h), (cx + w, y), (190, 160, 90), -1)
        cv2.addWeighted(liquid, 0.25, frame, 0.75, 0, frame)
        cv2.rectangle(frame, (cx - w, y - h), (cx + w, y), (230, 230, 235), 3, cv2.LINE_AA)
        text(frame, "H2O + dilute H2SO4", cx - 90, y + 26, 0.46, TEXT, 1, FONT_S)

    def _electrodes(self, frame, cx, y, running):
        for sx, name, col in ((-110, "CATHODE (−)", ACCENT), (110, "ANODE (+)", AMBER)):
            ex = cx + sx
            cv2.rectangle(frame, (ex - 9, y - 160), (ex + 9, y - 18),
                          (120, 120, 130), -1, cv2.LINE_AA)
            cv2.rectangle(frame, (ex - 9, y - 160), (ex + 9, y - 18), col, 2, cv2.LINE_AA)
            tw, _ = text_size(name, 0.42, 1, FONT_S)
            text(frame, name, ex - tw // 2, y - 172, 0.42, col, 1, FONT_S)
            if running:
                glow = frame.copy()
                cv2.rectangle(glow, (ex - 12, y - 160), (ex + 12, y - 18), col, -1)
                a = 0.10 + 0.06 * math.sin(time.time() * 6 + sx)
                cv2.addWeighted(glow, a, frame, 1 - a, 0, frame)

    def _battery(self, frame, cx, y, running):
        bx, by = cx, y - 300
        cv2.rectangle(frame, (bx - 46, by - 22), (bx + 46, by + 22), (60, 60, 70), -1, cv2.LINE_AA)
        cv2.rectangle(frame, (bx - 46, by - 22), (bx + 46, by + 22), AMBER, 2, cv2.LINE_AA)
        text(frame, "6 V DC", bx - 26, by + 7, 0.5, AMBER, 1, FONT_S)
        col = GREEN if running else MUTED
        cv2.line(frame, (bx - 46, by), (cx - 110, by), col, 2, cv2.LINE_AA)
        cv2.line(frame, (cx - 110, by), (cx - 110, y - 160), col, 2, cv2.LINE_AA)
        cv2.line(frame, (bx + 46, by), (cx + 110, by), col, 2, cv2.LINE_AA)
        cv2.line(frame, (cx + 110, by), (cx + 110, y - 160), col, 2, cv2.LINE_AA)
        if running:  # electron flow dots on wires
            u = (time.time() * 1.4) % 1.0
            yy = int(by + (y - 160 - by) * u)
            cv2.circle(frame, (cx - 110, yy), 3, GREEN, -1, cv2.LINE_AA)
            cv2.circle(frame, (cx + 110, y - 160 - int((y - 160 - by) * u)), 3, GREEN, -1, cv2.LINE_AA)

    def _bubbles(self, frame, cx, y):
        # spawn — cathode makes twice as many (H2 : O2 = 2 : 1)
        for side, n in ((-110, 2), (110, 1)):
            for _ in range(n):
                if self.rng.random() < 0.35:
                    self.bubbles.append([cx + side + self.rng.integers(-8, 9),
                                         y - 24, int(self.rng.integers(2, 5)),
                                         self.rng.uniform(1.2, 2.6)])
        alive = []
        for b in self.bubbles:
            b[1] -= b[3]
            if b[1] > y - 158:
                cv2.circle(frame, (int(b[0]), int(b[1])), b[2],
                           (255, 245, 230), 1, cv2.LINE_AA)
                alive.append(b)
        self.bubbles = alive[-160:]

    def _tubes(self, frame, cx, y, h2, o2):
        for sx, vol, name, col in ((-110, h2, "H2", ACCENT), (110, o2, "O2", AMBER)):
            tx = cx + sx
            top = y - 262
            cv2.rectangle(frame, (tx - 15, top), (tx + 15, y - 166),
                          (230, 230, 235), 2, cv2.LINE_AA)
            frac = min(vol / 40.0, 1.0)
            gh = int((y - 166 - top - 4) * frac)
            gas = frame.copy()
            cv2.rectangle(gas, (tx - 13, top + 2), (tx + 13, top + 2 + gh), col, -1)
            cv2.addWeighted(gas, 0.35, frame, 0.65, 0, frame)
            text(frame, f"{name} {vol:.1f} mL", tx - 34, top - 8, 0.44, col, 1, FONT_S)

    def _readout(self, frame, h2, o2, t):
        x0, y0 = self.W - 264, 92
        ratio = h2 / o2 if o2 > 0 else 0
        rows = [("TIME", f"{t:.0f} s", TEXT),
                ("H2 VOLUME", f"{h2:.1f} mL", ACCENT),
                ("O2 VOLUME", f"{o2:.1f} mL", AMBER),
                ("RATIO H2:O2", f"{ratio:.1f} : 1", GREEN)]
        glass_panel(frame, x0, y0, 248, 58 + 30 * len(rows), radius=16, border=ACCENT)
        text(frame, "LIVE ELECTROLYSIS", x0 + 16, y0 + 28, 0.5, ACCENT, 1, FONT_S)
        cv2.line(frame, (x0 + 16, y0 + 38), (x0 + 232, y0 + 38), (70, 60, 45), 1)
        for i, (k, v, col) in enumerate(rows):
            yy = y0 + 64 + i * 30
            text(frame, k, x0 + 16, yy, 0.44, MUTED, 1, FONT_S)
            vw, _ = text_size(v, 0.48, 1, FONT_S)
            text(frame, v, x0 + 232 - vw, yy, 0.48, col, 1, FONT_S)
        text(frame, "2 H2O -> 2 H2 + O2", x0 + 16, y0 + 58 + 30 * len(rows) + 22,
             0.5, PURPLE, 1, FONT_S)
