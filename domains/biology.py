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


# ═══════════════════════════════ neuron ════════════════════════════
class NeuronScene(Scene):
    """Neuron — action potential travelling down the axon, synapse firing."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)

    def render(self, frame):
        cx = int(self.W * 0.16); cy = int(self.H * 0.5)
        t = self.elapsed()
        fire = "fire" in self.animations

        # dendrites
        for a in range(-3, 4):
            ang = math.radians(120 + a * 22)
            ex = int(cx + math.cos(ang) * 70); ey = int(cy + math.sin(ang) * 70)
            cv2.line(frame, (cx, cy), (ex, ey), (150, 130, 200), 2, cv2.LINE_AA)
            cv2.line(frame, (ex, ey), (int(ex + math.cos(ang) * 24),
                     int(ey + math.sin(ang) * 24)), (150, 130, 200), 1, cv2.LINE_AA)

        # soma
        glow = frame.copy(); cv2.circle(glow, (cx, cy), 42, (200, 120, 180), -1)
        cv2.addWeighted(glow, 0.3, frame, 0.7, 0, frame)
        cv2.circle(frame, (cx, cy), 32, (170, 100, 160), -1, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), 14, (120, 60, 110), -1, cv2.LINE_AA)
        text(frame, "soma", cx - 18, cy + 58, 0.36, MUTED, 1, FONT_S)

        # axon
        axon_x2 = int(self.W * 0.72)
        cv2.line(frame, (cx + 32, cy), (axon_x2, cy), (180, 160, 210), 5, cv2.LINE_AA)
        # myelin sheaths
        for mx in range(cx + 80, axon_x2 - 40, 90):
            cv2.ellipse(frame, (mx, cy), (30, 14), 0, 0, 360, (150, 190, 240), -1, cv2.LINE_AA)
            cv2.ellipse(frame, (mx, cy), (30, 14), 0, 0, 360, (100, 130, 180), 1, cv2.LINE_AA)

        # action potential pulse
        if fire:
            prog = (t * 0.6) % 1.0
            px = int(cx + 32 + (axon_x2 - cx - 32) * prog)
            glow = frame.copy()
            cv2.circle(glow, (px, cy), 22, ACCENT, -1)
            cv2.addWeighted(glow, 0.5, frame, 0.5, 0, frame)
            cv2.circle(frame, (px, cy), 12, (255, 240, 150), -1, cv2.LINE_AA)
            chip(frame, "+40 mV", px - 24, cy - 44, ACCENT, 0.36)
            # synapse burst at the end
            if prog > 0.9:
                for _ in range(6):
                    a = np.random.uniform(0, 2 * math.pi)
                    r = np.random.uniform(6, 26)
                    nx = int(axon_x2 + math.cos(a) * r); ny = int(cy + math.sin(a) * r)
                    cv2.circle(frame, (nx, ny), 3, GREEN, -1, cv2.LINE_AA)

        # axon terminals
        for a in range(-2, 3):
            ang = math.radians(a * 24)
            ex = int(axon_x2 + math.cos(ang) * 34); ey = int(cy + math.sin(ang) * 34)
            cv2.line(frame, (axon_x2, cy), (ex, ey), (180, 160, 210), 2, cv2.LINE_AA)
            cv2.circle(frame, (ex, ey), 6, (150, 200, 160), -1, cv2.LINE_AA)

        # membrane potential trace
        gx, gy, gw, gh = _mini_scope(frame, self.W - 342, self.H - 210, 322, 165)
        pts = []
        for i in range(gw):
            tt = i / gw * 6 - (t * 2 % 6)
            # AP waveform
            v = -70
            x = (i / gw * 6 + t) % 6
            if 2 < x < 2.4: v = -70 + (x - 2) / 0.4 * 110
            elif 2.4 <= x < 2.9: v = 40 - (x - 2.4) / 0.5 * 115
            elif 2.9 <= x < 3.4: v = -75 + (x - 2.9) / 0.5 * 5
            pts.append((gx + i, int(gy + gh * (1 - (v + 80) / 130))))
        cv2.polylines(frame, [np.array(pts, np.int32)], False, GREEN, 2, cv2.LINE_AA)

        x0 = self.W - 264; y0 = 92
        rows = [("RESTING", "-70 mV", ACCENT),
                ("THRESHOLD", "-55 mV", AMBER),
                ("PEAK", "+40 mV", RED),
                ("SIGNAL", "FIRING" if fire else "resting", GREEN if fire else MUTED)]
        glass_panel(frame, x0, y0, 248, 58 + 30 * len(rows), radius=16, border=PURPLE)
        text(frame, "ACTION POTENTIAL", x0 + 16, y0 + 28, 0.5, PURPLE, 1, FONT_S)
        cv2.line(frame, (x0 + 16, y0 + 38), (x0 + 232, y0 + 38), (70, 60, 45), 1)
        for i, (k, v, c) in enumerate(rows):
            yy = y0 + 64 + i * 30
            text(frame, k, x0 + 16, yy, 0.44, MUTED, 1, FONT_S)
            vw, _ = text_size(v, 0.48, 1, FONT_S)
            text(frame, v, x0 + 232 - vw, yy, 0.48, c, 1, FONT_S)
        return frame


def _mini_scope(frame, x, y, w, h):
    glass_panel(frame, x, y, w, h, radius=12, border=GREEN)
    text(frame, "MEMBRANE POTENTIAL (mV)", x + 12, y + 20, 0.38, GREEN, 1, FONT_S)
    gx, gy, gw, gh = x + 12, y + 28, w - 24, h - 42
    for i in range(1, 4):
        cv2.line(frame, (gx, gy + gh * i // 4), (gx + gw, gy + gh * i // 4), (50, 55, 45), 1)
    return gx, gy, gw, gh


# ═══════════════════════════ photosynthesis ════════════════════════
class PhotosynthesisScene(Scene):
    """Photosynthesis — light + CO2 + H2O -> glucose + O2 inside a leaf/chloroplast."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.rng = np.random.default_rng(6)
        self.o2 = []

    def render(self, frame):
        cx, cy = int(self.W * 0.40), int(self.H * 0.52)
        t = self.elapsed()
        active = "run" in self.animations

        # chloroplast body
        ov = frame.copy()
        cv2.ellipse(ov, (cx, cy), (240, 150), 0, 0, 360, (60, 160, 90), -1)
        cv2.addWeighted(ov, 0.18, frame, 0.82, 0, frame)
        cv2.ellipse(frame, (cx, cy), (240, 150), 0, 0, 360, (100, 220, 130), 2, cv2.LINE_AA)

        # thylakoid stacks (grana)
        for gx in (cx - 120, cx - 40, cx + 60, cx + 150):
            for k in range(4):
                cv2.ellipse(frame, (gx, cy - 30 + k * 18), (26, 8), 0, 0, 360,
                            (70, 180, 110), -1, cv2.LINE_AA)
                cv2.ellipse(frame, (gx, cy - 30 + k * 18), (26, 8), 0, 0, 360,
                            (40, 120, 70), 1, cv2.LINE_AA)

        # sunlight photons streaming in
        if active:
            for k in range(6):
                sx = int(self.W * 0.1 + ((t * 200 + k * 90) % (cx - 120)))
                sy = int(self.H * 0.12 + k * 12)
                cv2.line(frame, (sx, sy), (sx + 30, sy + 40), (0, 220, 255), 2, cv2.LINE_AA)
            text(frame, "SUNLIGHT", int(self.W * 0.1), int(self.H * 0.1), 0.44, AMBER, 1, FONT_S)

            # CO2 in from left, H2O from bottom
            chip(frame, "CO₂ in", cx - 300, cy, (150, 150, 160), 0.4)
            chip(frame, "H₂O in", cx - 60, cy + 170, (255, 180, 120), 0.4)

            # O2 bubbles out top-right
            if self.rng.random() < 0.4:
                self.o2.append([cx + 180, cy - 60, self.rng.uniform(1.5, 3)])
            alive = []
            for b in self.o2:
                b[1] -= b[2]; b[0] += 1
                if b[1] > int(self.H * 0.1):
                    cv2.circle(frame, (int(b[0]), int(b[1])), 6, (255, 220, 120), 1, cv2.LINE_AA)
                    text(frame, "O₂", int(b[0]) - 8, int(b[1]) + 4, 0.32, GREEN, 1, FONT_S, shadow=False)
                    alive.append(b)
            self.o2 = alive[-30:]

            # glucose forming in centre
            pulse = 0.5 + 0.5 * math.sin(t * 3)
            cv2.circle(frame, (cx, cy), int(20 + 6 * pulse), (80, 200, 255), 2, cv2.LINE_AA)
            text(frame, "C₆H₁₂O₆", cx - 34, cy + 4, 0.4, AMBER, 1, FONT_S)

        x0 = self.W - 264; y0 = 92
        rows = [("LIGHT", "absorbed" if active else "—", AMBER if active else MUTED),
                ("CO₂ + H₂O", "inputs", ACCENT),
                ("GLUCOSE", "produced" if active else "—", GREEN if active else MUTED),
                ("O₂", "released" if active else "—", GREEN if active else MUTED)]
        glass_panel(frame, x0, y0, 248, 58 + 30 * len(rows) + 30, radius=16, border=GREEN)
        text(frame, "PHOTOSYNTHESIS", x0 + 16, y0 + 28, 0.5, GREEN, 1, FONT_S)
        cv2.line(frame, (x0 + 16, y0 + 38), (x0 + 232, y0 + 38), (70, 60, 45), 1)
        for i, (k, v, c) in enumerate(rows):
            yy = y0 + 64 + i * 30
            text(frame, k, x0 + 16, yy, 0.44, MUTED, 1, FONT_S)
            vw, _ = text_size(v, 0.48, 1, FONT_S)
            text(frame, v, x0 + 232 - vw, yy, 0.48, c, 1, FONT_S)
        text(frame, "6CO₂+6H₂O→C₆H₁₂O₆+6O₂", x0 + 12, y0 + 64 + 30 * len(rows) + 18,
             0.4, PURPLE, 1, FONT_S)
        return frame
