# domains/circuits.py
"""
Circuit scenes — proper CircuitVerse experiments drawn as live vector
circuits with animated analog meters (ammeter / voltmeter), glowing wires,
and current-flow particles. Physics comes from circuit_engine.solver.

  OhmsLawScene       — V source, R, ammeter (series) + voltmeter (parallel)
  SeriesResistorScene— three R in series, ammeter, per-resistor voltmeters
  ParallelResistorScene — two R in parallel, branch ammeters
  WheatstoneScene    — Wheatstone bridge with galvanometer null detection
"""

import math
import time
import cv2
import numpy as np

from hud import (ACCENT, PURPLE, GREEN, AMBER, RED, TEXT, MUTED,
                 glass_panel, text, text_size, chip, FONT_S)
from . import Scene

WIRE = (120, 220, 140)
COPPER = (90, 150, 230)


# ─────────────────────── shared drawing toolkit ───────────────────────
def _node(frame, x, y):
    cv2.circle(frame, (x, y), 5, (210, 210, 220), -1, cv2.LINE_AA)


def wire(frame, p1, p2, live=True, t=0.0, current=0.0):
    """Glowing orthogonal-friendly wire with optional current particles."""
    col = WIRE if live else (80, 95, 85)
    if live:
        ov = frame.copy()
        cv2.line(ov, p1, p2, col, 8, cv2.LINE_AA)
        cv2.addWeighted(ov, 0.22, frame, 0.78, 0, frame)
    cv2.line(frame, p1, p2, (30, 55, 35), 5, cv2.LINE_AA)
    cv2.line(frame, p1, p2, col, 2, cv2.LINE_AA)
    if live and current > 1e-6:
        length = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        n = max(1, int(length / 60))
        speed = min(0.25 + current * 30, 1.2)
        for k in range(n):
            u = ((t * speed) + k / n) % 1.0
            x = int(p1[0] + (p2[0] - p1[0]) * u)
            y = int(p1[1] + (p2[1] - p1[1]) * u)
            cv2.circle(frame, (x, y), 3, (150, 255, 190), -1, cv2.LINE_AA)
            cv2.circle(frame, (x, y), 6, (70, 200, 110), 1, cv2.LINE_AA)


def battery(frame, x, y, label="V1", volts=None):
    """DC source symbol (long/short plates), vertical orientation."""
    cv2.line(frame, (x, y - 26), (x, y - 10), (210, 210, 220), 2, cv2.LINE_AA)
    cv2.line(frame, (x - 20, y - 10), (x + 20, y - 10), AMBER, 3, cv2.LINE_AA)  # long +
    cv2.line(frame, (x - 10, y + 2), (x + 10, y + 2), (210, 210, 220), 3, cv2.LINE_AA)  # short -
    cv2.line(frame, (x - 20, y + 14), (x + 20, y + 14), AMBER, 3, cv2.LINE_AA)
    cv2.line(frame, (x - 10, y + 26), (x + 10, y + 26), (210, 210, 220), 3, cv2.LINE_AA)
    cv2.line(frame, (x, y + 26), (x, y + 42), (210, 210, 220), 2, cv2.LINE_AA)
    text(frame, "+", x + 24, y - 6, 0.5, AMBER, 1, FONT_S)
    text(frame, "-", x + 24, y + 30, 0.5, MUTED, 1, FONT_S)
    lbl = f"{label}" + (f"  {volts:.0f}V" if volts is not None else "")
    text(frame, lbl, x - 60, y + 6, 0.46, TEXT, 1, FONT_S)


def resistor(frame, x, y, label="R", ohms=None, horizontal=True, hot=False):
    """Zig-zag resistor centred at (x,y)."""
    col = (255, 180, 80) if hot else CYAN_R
    n = 6
    span = 70
    pts = []
    if horizontal:
        x0 = x - span // 2
        pts.append((x0, y))
        for i in range(n):
            pts.append((x0 + int(span * (i + 0.5) / n),
                        y - 12 if i % 2 == 0 else y + 12))
        pts.append((x + span // 2, y))
    else:
        y0 = y - span // 2
        pts.append((x, y0))
        for i in range(n):
            pts.append((x - 12 if i % 2 == 0 else x + 12,
                        y0 + int(span * (i + 0.5) / n)))
        pts.append((x, y + span // 2))
    cv2.polylines(frame, [np.array(pts, np.int32)], False, col, 3, cv2.LINE_AA)
    lbl = f"{label}" + (f"  {_fmt_ohm(ohms)}" if ohms is not None else "")
    if horizontal:
        tw, _ = text_size(lbl, 0.44, 1, FONT_S)
        text(frame, lbl, x - tw // 2, y - 22, 0.44, TEXT, 1, FONT_S)
    else:
        text(frame, lbl, x + 22, y, 0.44, TEXT, 1, FONT_S)


CYAN_R = (255, 212, 0)


def _fmt_ohm(o):
    if o is None:
        return ""
    return f"{o/1000:.1f}k\u03a9" if o >= 1000 else f"{o:.0f}\u03a9"


def meter(frame, x, y, kind, value, unit, t, label, color=ACCENT, r=44):
    """Analog dial meter (ammeter 'A' / voltmeter 'V') with a swinging needle."""
    # glass bezel
    glass_panel(frame, x - r - 6, y - r - 6, 2 * r + 12, 2 * r + 30,
                radius=14, border=color, tint_strength=0.5, blur=9)
    # dial face
    cv2.circle(frame, (x, y), r, (18, 22, 30), -1, cv2.LINE_AA)
    cv2.circle(frame, (x, y), r, color, 2, cv2.LINE_AA)
    # scale ticks
    for a in range(-60, 61, 15):
        ang = math.radians(a - 90)
        x1 = int(x + math.cos(ang) * (r - 8)); y1 = int(y + math.sin(ang) * (r - 8))
        x2 = int(x + math.cos(ang) * (r - 2)); y2 = int(y + math.sin(ang) * (r - 2))
        cv2.line(frame, (x1, y1), (x2, y2), (120, 130, 145), 1, cv2.LINE_AA)
    # needle — map value to -60..+60 deg against a per-unit reference
    ref = 0.05 if unit == "A" else 12.0
    disp = min(value / ref, 1.0) if ref else 0.0
    wobble = math.sin(t * 8) * 2 if value > 0 else 0
    ang = math.radians((-60 + disp * 120) - 90 + wobble)
    nx = int(x + math.cos(ang) * (r - 10)); ny = int(y + math.sin(ang) * (r - 10))
    cv2.line(frame, (x, y), (nx, ny), RED, 2, cv2.LINE_AA)
    cv2.circle(frame, (x, y), 4, (200, 200, 210), -1, cv2.LINE_AA)
    # big letter
    text(frame, kind, x - 8, y + r - 12, 0.6, color, 1, FONT_S)
    # readout
    val = f"{value*1000:.1f} mA" if unit == "A" and value < 1 else f"{value:.2f} {unit}"
    tw, _ = text_size(val, 0.5, 1, FONT_S)
    text(frame, val, x - tw // 2, y + r + 20, 0.5, color, 1, FONT_S)
    tw2, _ = text_size(label, 0.36, 1, FONT_S)
    text(frame, label, x - tw2 // 2, y - r - 10, 0.36, MUTED, 1, FONT_S, shadow=False)


def _panel(frame, W, rows, title, border=ACCENT, y0=92):
    x0 = W - 264
    h = 58 + 30 * len(rows)
    glass_panel(frame, x0, y0, 248, h, radius=16, border=border)
    text(frame, title, x0 + 16, y0 + 28, 0.5, border, 1, FONT_S)
    cv2.line(frame, (x0 + 16, y0 + 38), (x0 + 232, y0 + 38), (70, 60, 45), 1)
    for i, (k, v, col) in enumerate(rows):
        yy = y0 + 64 + i * 30
        text(frame, k, x0 + 16, yy, 0.44, MUTED, 1, FONT_S)
        vw, _ = text_size(v, 0.48, 1, FONT_S)
        text(frame, v, x0 + 232 - vw, yy, 0.48, col, 1, FONT_S)


# ═══════════════════════════════ Ohm's law ═════════════════════════
class OhmsLawScene(Scene):
    """Series battery–ammeter–resistor loop with a voltmeter across R."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.V = self.sim.get("voltage", 6.0)
        self.R = self.sim.get("resistance", 100.0)

    def render(self, frame):
        t = self.elapsed()
        live = "measure" in self.animations or self.current_step_live()
        I = self.V / self.R if live else 0.0

        # loop rectangle
        L, Rr = int(self.W * 0.24), int(self.W * 0.60)
        Top, Bot = int(self.H * 0.36), int(self.H * 0.62)
        midY = (Top + Bot) // 2

        # battery on the left edge (vertical), its wires become the left side
        battery(frame, L, midY - 8, "V1", self.V)
        wire(frame, (L, midY - 34), (L, Top), live, t, I)      # + up to top-left
        wire(frame, (L, midY + 42), (L, Bot), live, t, I)      # - down to bot-left

        # top run: top-left -> ammeter -> resistor -> top-right
        am_x = L + 130
        r_x = Rr - 120
        wire(frame, (L, Top), (am_x - 50, Top), live, t, I)
        meter(frame, am_x, Top, "A", I, "A", t, "AMMETER (series)", ACCENT)
        wire(frame, (am_x + 50, Top), (r_x - 45, Top), live, t, I)
        resistor(frame, r_x, Top, "R1", self.R, horizontal=True, hot=live)
        wire(frame, (r_x + 45, Top), (Rr, Top), live, t, I)

        # right + bottom back to battery
        wire(frame, (Rr, Top), (Rr, Bot), live, t, I)
        wire(frame, (Rr, Bot), (L, Bot), live, t, I)
        for nx, ny in [(L, Top), (Rr, Top), (L, Bot), (Rr, Bot)]:
            _node(frame, nx, ny)

        # voltmeter in parallel across R — taps just outside each resistor lead,
        # drops straight down to a meter below the loop (no crossing)
        tapL, tapR = r_x - 45, r_x + 45
        vm_y = Bot + 70
        wire(frame, (tapL, Top), (tapL, vm_y), live, t, 0)
        wire(frame, (tapR, Top), (tapR, vm_y), live, t, 0)
        wire(frame, (tapL, vm_y), (r_x - 50, vm_y), live, t, 0)
        wire(frame, (tapR, vm_y), (r_x + 50, vm_y), live, t, 0)
        _node(frame, tapL, Top); _node(frame, tapR, Top)
        meter(frame, r_x, vm_y, "V", self.V if live else 0.0, "V", t,
              "VOLTMETER (parallel)", AMBER)

        _panel(frame, self.W, [
            ("SUPPLY", f"{self.V:.1f} V", AMBER),
            ("RESISTANCE", _fmt_ohm(self.R), CYAN_R),
            ("CURRENT (A)", f"{I*1000:.1f} mA", ACCENT),
            ("V ACROSS R", f"{self.V if live else 0:.2f} V", GREEN),
            ("OHM CHECK", "V = IR ✓" if live else "open", GREEN if live else MUTED),
        ], "OHM'S LAW")
        return frame

    def current_step_live(self):
        # circuit is 'live' once the measure/observe step is reached
        return len(self.animations) > 0


# ═══════════════════════════ series resistors ══════════════════════
class SeriesResistorScene(Scene):
    """Three resistors in series; one ammeter; a voltmeter reading each drop."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.V = self.sim.get("voltage", 12.0)
        self.Rs = self.sim.get("resistors", [220, 330, 470])

    def render(self, frame):
        t = self.elapsed()
        live = len(self.animations) > 0
        Rtot = sum(self.Rs)
        I = self.V / Rtot if live else 0.0

        L, Rr = int(self.W * 0.18), int(self.W * 0.66)
        Top, Bot = int(self.H * 0.34), int(self.H * 0.66)
        battery(frame, L, (Top + Bot)//2 - 8, "V1", self.V)
        wire(frame, (L, (Top+Bot)//2 - 34), (L, Top), live, t, I)
        wire(frame, (L, (Top+Bot)//2 + 42), (L, Bot), live, t, I)

        # ammeter then three resistors spaced along the top
        am_x = L + 90
        meter(frame, am_x, Top, "A", I, "A", t, "AMMETER", ACCENT)
        wire(frame, (L, Top), (am_x - 50, Top), live, t, I)
        xs = np.linspace(am_x + 110, Rr - 30, len(self.Rs))
        prev = am_x + 50
        drops = []
        for i, (rx, R) in enumerate(zip(xs, self.Rs)):
            rx = int(rx)
            wire(frame, (prev, Top), (rx - 45, Top), live, t, I)
            resistor(frame, rx, Top, f"R{i+1}", R, horizontal=True, hot=live)
            drops.append(I * R)
            prev = rx + 45
        wire(frame, (prev, Top), (Rr, Top), live, t, I)
        wire(frame, (Rr, Top), (Rr, Bot), live, t, I)
        wire(frame, (Rr, Bot), (L, Bot), live, t, I)

        # voltmeter across R2 (middle)
        mid_x = int(xs[1])
        vm_y = Bot + 6
        wire(frame, (mid_x - 45, Top), (mid_x - 45, vm_y - 40), live, t, 0)
        wire(frame, (mid_x + 45, Top), (mid_x + 45, vm_y - 40), live, t, 0)
        meter(frame, mid_x, vm_y, "V", drops[1] if live else 0.0, "V", t,
              "VOLTMETER across R2", AMBER)

        rows = [("SUPPLY", f"{self.V:.0f} V", AMBER),
                ("TOTAL R", _fmt_ohm(Rtot), CYAN_R),
                ("CURRENT", f"{I*1000:.1f} mA", ACCENT)]
        for i, d in enumerate(drops):
            rows.append((f"V(R{i+1})", f"{d:.2f} V", GREEN))
        _panel(frame, self.W, rows, "SERIES CIRCUIT")
        return frame


# ══════════════════════════ parallel resistors ═════════════════════
class ParallelResistorScene(Scene):
    """Two resistors in parallel, each branch with its own ammeter."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.V = self.sim.get("voltage", 6.0)
        self.R1 = self.sim.get("r1", 100.0)
        self.R2 = self.sim.get("r2", 200.0)

    def render(self, frame):
        t = self.elapsed()
        live = len(self.animations) > 0
        I1 = self.V / self.R1 if live else 0.0
        I2 = self.V / self.R2 if live else 0.0
        Itot = I1 + I2
        Req = 1 / (1/self.R1 + 1/self.R2)

        L = int(self.W * 0.20)
        Xj1, Xj2 = int(self.W * 0.40), int(self.W * 0.64)   # junction columns
        Top, Bot = int(self.H * 0.30), int(self.H * 0.72)
        midT, midB = int(self.H * 0.42), int(self.H * 0.60)

        battery(frame, L, (Top + Bot)//2 - 8, "V1", self.V)
        wire(frame, (L, (Top+Bot)//2 - 34), (L, midT), live, t, Itot)
        # main ammeter before the split
        meter(frame, (L + Xj1)//2, midT, "A", Itot, "A", t, "TOTAL", ACCENT)
        wire(frame, (L, midT), ((L+Xj1)//2 - 50, midT), live, t, Itot)
        wire(frame, ((L+Xj1)//2 + 50, midT), (Xj1, midT), live, t, Itot)

        # split node
        wire(frame, (Xj1, midT), (Xj1, midB), live, t, Itot)
        _node(frame, Xj1, midT); _node(frame, Xj1, midB)

        # branch 1 (upper)
        wire(frame, (Xj1, midT), (Xj1 + 40, midT), live, t, I1)
        resistor(frame, (Xj1 + Xj2)//2, midT, "R1", self.R1, True, live)
        wire(frame, ((Xj1+Xj2)//2 + 45, midT), (Xj2, midT), live, t, I1)
        # branch 1 ammeter
        meter(frame, Xj2 + 54, midT, "A", I1, "A", t, "R1", GREEN, r=34)

        # branch 2 (lower)
        wire(frame, (Xj1, midB), (Xj1 + 40, midB), live, t, I2)
        resistor(frame, (Xj1 + Xj2)//2, midB, "R2", self.R2, True, live)
        wire(frame, ((Xj1+Xj2)//2 + 45, midB), (Xj2, midB), live, t, I2)
        meter(frame, Xj2 + 54, midB, "A", I2, "A", t, "R2", GREEN, r=34)

        # rejoin
        wire(frame, (Xj2 + 88, midT), (Xj2 + 120, midT), live, t, I1)
        wire(frame, (Xj2 + 88, midB), (Xj2 + 120, midB), live, t, I2)
        wire(frame, (Xj2 + 120, midT), (Xj2 + 120, midB), live, t, Itot)
        wire(frame, (Xj2 + 120, (midT+midB)//2), (Xj2 + 120, Bot), live, t, Itot)
        wire(frame, (Xj2 + 120, Bot), (L, Bot), live, t, Itot)
        wire(frame, (L, Bot), (L, (Top+Bot)//2 + 42), live, t, Itot)

        _panel(frame, self.W, [
            ("SUPPLY", f"{self.V:.1f} V", AMBER),
            ("R1 / R2", f"{_fmt_ohm(self.R1)}/{_fmt_ohm(self.R2)}", CYAN_R),
            ("R equiv", _fmt_ohm(Req), PURPLE),
            ("I(R1)", f"{I1*1000:.1f} mA", GREEN),
            ("I(R2)", f"{I2*1000:.1f} mA", GREEN),
            ("I total", f"{Itot*1000:.1f} mA", ACCENT),
        ], "PARALLEL CIRCUIT")
        return frame


# ═══════════════════════════ Wheatstone bridge ═════════════════════
class WheatstoneScene(Scene):
    """Wheatstone bridge — galvanometer nulls when R1/R2 = R3/Rx."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.V = self.sim.get("voltage", 6.0)
        self.R1 = self.sim.get("r1", 100.0)
        self.R2 = self.sim.get("r2", 100.0)
        self.R3 = self.sim.get("r3", 150.0)
        self.Rx = self.sim.get("rx", 150.0)

    def render(self, frame):
        t = self.elapsed()
        live = len(self.animations) > 0
        # bridge geometry (diamond)
        cx, cy = int(self.W * 0.40), int(self.H * 0.52)
        top = (cx, cy - 130); bot = (cx, cy + 130)
        lft = (cx - 150, cy); rgt = (cx + 150, cy)

        # galvanometer deflection ~ bridge imbalance
        bal = (self.R1 * self.Rx - self.R2 * self.R3)
        denom = (self.R1 + self.R2) * (self.R3 + self.Rx)
        defl = (bal / denom) if denom else 0
        nulled = abs(defl) < 1e-3

        for a, b, I_on in [(top, lft, live), (top, rgt, live),
                           (lft, bot, live), (rgt, bot, live)]:
            wire(frame, a, b, I_on, t, 0.02 if live else 0)
        # arms with resistors at midpoints
        resistor(frame, (top[0]+lft[0])//2, (top[1]+lft[1])//2, "R1", self.R1, False, live)
        resistor(frame, (top[0]+rgt[0])//2, (top[1]+rgt[1])//2, "R2", self.R2, False, live)
        resistor(frame, (lft[0]+bot[0])//2, (lft[1]+bot[1])//2, "R3", self.R3, False, live)
        resistor(frame, (rgt[0]+bot[0])//2, (rgt[1]+bot[1])//2, "Rx", self.Rx, False, live)

        # galvanometer across the bridge (lft-rgt)
        gx, gy = cx, cy
        wire(frame, lft, (gx - 40, gy), live, t, 0)
        wire(frame, (gx + 40, gy), rgt, live, t, 0)
        # galvo dial
        glass_panel(frame, gx - 40, gy - 34, 80, 68, radius=12, border=ACCENT)
        cv2.ellipse(frame, (gx, gy + 6), (28, 28), 0, 180, 360, (90, 100, 115), 1, cv2.LINE_AA)
        ang = math.radians(90 - max(-80, min(80, defl * 900)))
        nx = int(gx + math.cos(ang) * 24); ny = int(gy + 6 - math.sin(ang) * 24)
        col = GREEN if nulled else RED
        cv2.line(frame, (gx, gy + 6), (nx, ny), col, 2, cv2.LINE_AA)
        text(frame, "G", gx - 5, gy - 16, 0.5, ACCENT, 1, FONT_S)

        # battery across top-bottom
        battery(frame, cx, bot[1] + 60, "V1", self.V)
        wire(frame, top, (top[0], top[1] - 40), live, t, 0.02 if live else 0)
        wire(frame, (top[0], top[1] - 40), (cx - 220, top[1] - 40), live, t, 0)
        wire(frame, (cx - 220, top[1] - 40), (cx - 220, bot[1] + 60), live, t, 0)
        wire(frame, (cx - 220, bot[1] + 60), (cx - 20, bot[1] + 60), live, t, 0)
        wire(frame, (cx + 20, bot[1] + 60), (cx + 40, bot[1] + 60), live, t, 0)
        wire(frame, bot, (bot[0], bot[1] + 34), live, t, 0)

        if nulled:
            chip(frame, "BRIDGE BALANCED — G reads 0", cx - 90, cy + 150, GREEN, 0.42)

        _panel(frame, self.W, [
            ("SUPPLY", f"{self.V:.0f} V", AMBER),
            ("R1 / R2", f"{_fmt_ohm(self.R1)}/{_fmt_ohm(self.R2)}", CYAN_R),
            ("R3 (known)", _fmt_ohm(self.R3), CYAN_R),
            ("Rx (unknown)", _fmt_ohm(self.Rx), PURPLE),
            ("GALVO", "NULL ✓" if nulled else "deflected", GREEN if nulled else RED),
            ("BALANCE", "R1·Rx = R2·R3", MUTED),
        ], "WHEATSTONE BRIDGE")
        return frame
