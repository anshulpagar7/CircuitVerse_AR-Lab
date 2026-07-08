# domains/physics.py
"""
Physics scenes — drawn as live vector simulations (no asset PNGs).
Each scene includes proper instruments (oscilloscope, meters, screens).

  SHMScene         — mass-spring SHM + oscilloscope trace
  ResonanceScene   — driven oscillator amplitude vs frequency, resonance peak
  InterferenceScene— double-slit wavefronts + intensity fringes on a screen
  LensScene        — converging lens ray diagram, live image formation
  RefractionScene  — Snell's law at an interface, live bending + TIR
  MotorScene       — DC motor: field, current, force (F = BIL), rotation
  InductionScene   — magnet through coil, Faraday EMF on a galvanometer
  PhotoelectricScene— photons ejecting electrons, stopping voltage
  BohrScene        — hydrogen energy levels, electron jumps, photon emission
"""

import math
import time
import cv2
import numpy as np

from hud import (ACCENT, PURPLE, GREEN, AMBER, RED, TEXT, MUTED,
                 glass_panel, text, text_size, chip, FONT_S)
from . import Scene

CYAN = (255, 212, 0)
HOT  = (80, 120, 240)


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


def _scope(frame, x, y, w, h, border=GREEN, label="OSCILLOSCOPE"):
    glass_panel(frame, x, y, w, h, radius=14, border=border)
    text(frame, label, x + 14, y + 22, 0.42, border, 1, FONT_S)
    gx, gy, gw, gh = x + 14, y + 32, w - 28, h - 46
    # grid
    for i in range(1, 6):
        cv2.line(frame, (gx + gw * i // 6, gy), (gx + gw * i // 6, gy + gh),
                 (50, 55, 45), 1)
        cv2.line(frame, (gx, gy + gh * i // 6), (gx + gw, gy + gh * i // 6),
                 (50, 55, 45), 1)
    cv2.line(frame, (gx, gy + gh // 2), (gx + gw, gy + gh // 2), (80, 90, 70), 1)
    return gx, gy, gw, gh


# ═══════════════════════════════ SHM ═══════════════════════════════
class SHMScene(Scene):
    """Mass on a spring — simple harmonic motion with a live scope trace."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.k = self.sim.get("k", 20.0)
        self.m = self.sim.get("mass_kg", 0.5)
        self.A = self.sim.get("amplitude_m", 0.12)
        self.omega = math.sqrt(self.k / self.m)
        self.trace = []

    def render(self, frame):
        cx = int(self.W * 0.30)
        ceil_y = int(self.H * 0.24)
        t = self.elapsed() if "oscillate" in self.animations else 0.0
        disp = self.A * math.cos(self.omega * t)
        scale = 520
        bob_y = int(self.H * 0.52 + disp * scale)

        # ceiling mount
        cv2.line(frame, (cx - 80, ceil_y), (cx + 80, ceil_y), (150, 150, 160), 5, cv2.LINE_AA)
        for hx in range(cx - 70, cx + 71, 20):
            cv2.line(frame, (hx, ceil_y), (hx - 10, ceil_y - 12), (110, 110, 120), 2, cv2.LINE_AA)

        # spring (zig-zag) from ceiling to bob
        self._spring(frame, cx, ceil_y, bob_y - 34)

        # equilibrium guide
        eq = int(self.H * 0.52)
        cv2.line(frame, (cx + 60, eq), (cx + 120, eq), (70, 80, 95), 1, cv2.LINE_AA)
        chip(frame, "equilibrium", cx + 70, eq - 24, MUTED, 0.36)

        # mass
        glow = frame.copy()
        cv2.circle(glow, (cx, bob_y), 40, AMBER, -1)
        cv2.addWeighted(glow, 0.28, frame, 0.72, 0, frame)
        cv2.rectangle(frame, (cx - 30, bob_y - 30), (cx + 30, bob_y + 30),
                      (40, 120, 220), -1, cv2.LINE_AA)
        cv2.rectangle(frame, (cx - 30, bob_y - 30), (cx + 30, bob_y + 30),
                      AMBER, 2, cv2.LINE_AA)
        text(frame, f"{self.m:.1f} kg", cx - 26, bob_y + 6, 0.5, TEXT, 1, FONT_S)

        # velocity arrow
        v = -self.A * self.omega * math.sin(self.omega * t)
        if abs(v) > 0.02:
            vy = int(bob_y + v * scale * 0.3)
            cv2.arrowedLine(frame, (cx + 44, bob_y), (cx + 44, vy), GREEN, 3,
                            cv2.LINE_AA, tipLength=0.3)

        # scope trace
        gx, gy, gw, gh = _scope(frame, self.W - 342, self.H - 250, 322, 205)
        self.trace.append(disp / self.A)
        self.trace = self.trace[-gw:]
        pts = [(gx + i, int(gy + gh / 2 - v * gh / 2 * 0.9))
               for i, v in enumerate(self.trace)]
        if len(pts) > 1:
            cv2.polylines(frame, [np.array(pts, np.int32)], False, GREEN, 2, cv2.LINE_AA)

        T = 2 * math.pi / self.omega
        _panel(frame, self.W, [
            ("SPRING k", f"{self.k:.0f} N/m", ACCENT),
            ("MASS", f"{self.m:.1f} kg", TEXT),
            ("DISPLACEMENT", f"{disp*100:+.1f} cm", AMBER),
            ("VELOCITY", f"{v:+.2f} m/s", GREEN),
            ("PERIOD T", f"{T:.2f} s", PURPLE),
        ], "SHM PHYSICS")
        return frame

    def _spring(self, frame, cx, y0, y1):
        coils = 12
        pts = [(cx, y0)]
        seg = (y1 - y0) / (coils + 1)
        for i in range(1, coils + 1):
            pts.append((cx + (22 if i % 2 else -22), int(y0 + seg * i)))
        pts.append((cx, y1))
        cv2.polylines(frame, [np.array(pts, np.int32)], False,
                      (180, 190, 210), 2, cv2.LINE_AA)


# ══════════════════════════ resonance ══════════════════════════════
class ResonanceScene(Scene):
    """Driven damped oscillator — amplitude vs drive frequency curve."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.f0 = self.sim.get("natural_freq", 2.0)
        self.damping = self.sim.get("damping", 0.18)

    def _amp(self, f):
        r = f / self.f0
        return 1.0 / math.sqrt((1 - r * r) ** 2 + (2 * self.damping * r) ** 2)

    def render(self, frame):
        # sweeping drive frequency
        t = self.elapsed() if "sweep" in self.animations else 0.0
        f_drive = 0.3 + (t * 0.35) % (self.f0 * 2)
        amp = self._amp(f_drive)
        amp_max = self._amp(self.f0)

        # driven oscillator visual (mass wobbling with current amplitude)
        cx, cy = int(self.W * 0.30), int(self.H * 0.5)
        wob = math.sin(t * f_drive * 6) * amp / amp_max * 80
        cv2.line(frame, (cx - 120, cy), (cx + int(wob), cy), (150, 160, 180), 3, cv2.LINE_AA)
        glow = frame.copy()
        cv2.circle(glow, (cx + int(wob), cy), 34, AMBER, -1)
        cv2.addWeighted(glow, 0.3, frame, 0.7, 0, frame)
        cv2.circle(frame, (cx + int(wob), cy), 24, HOT, -1, cv2.LINE_AA)
        cv2.circle(frame, (cx + int(wob), cy), 24, AMBER, 2, cv2.LINE_AA)

        # resonance curve
        x0, y0, w, h = self.W - 360, self.H - 280, 340, 235
        glass_panel(frame, x0, y0, w, h, radius=14, border=PURPLE)
        text(frame, "RESONANCE CURVE", x0 + 14, y0 + 24, 0.45, PURPLE, 1, FONT_S)
        gx, gy, gw, gh = x0 + 30, y0 + 34, w - 48, h - 60
        cv2.line(frame, (gx, gy + gh), (gx + gw, gy + gh), MUTED, 1, cv2.LINE_AA)
        cv2.line(frame, (gx, gy), (gx, gy + gh), MUTED, 1, cv2.LINE_AA)
        fmax = self.f0 * 2
        pts = []
        for i in range(gw):
            f = fmax * i / gw
            a = self._amp(f) / amp_max
            pts.append((gx + i, int(gy + gh - a * gh * 0.92)))
        cv2.polylines(frame, [np.array(pts, np.int32)], False, PURPLE, 2, cv2.LINE_AA)
        # resonance line
        rx = gx + int(gw * self.f0 / fmax)
        for yy in range(gy, gy + gh, 8):
            cv2.line(frame, (rx, yy), (rx, yy + 4), (120, 90, 160), 1)
        text(frame, "f0", rx - 8, gy + gh + 16, 0.4, PURPLE, 1, FONT_S, shadow=False)
        # live marker
        mx = gx + int(gw * f_drive / fmax)
        my = int(gy + gh - (amp / amp_max) * gh * 0.92)
        cv2.circle(frame, (mx, my), 6, ACCENT, -1, cv2.LINE_AA)
        cv2.circle(frame, (mx, my), 10, ACCENT, 1, cv2.LINE_AA)

        near = abs(f_drive - self.f0) < 0.15
        _panel(frame, self.W, [
            ("NATURAL f0", f"{self.f0:.2f} Hz", PURPLE),
            ("DRIVE FREQ", f"{f_drive:.2f} Hz", ACCENT),
            ("AMPLITUDE", f"{amp/amp_max*100:.0f}%", RED if near else GREEN),
            ("DAMPING", f"{self.damping:.2f}", TEXT),
            ("STATE", "RESONANCE!" if near else "driving", RED if near else MUTED),
        ], "DRIVEN OSCILLATOR")
        return frame


# ═════════════════════════ interference ════════════════════════════
class InterferenceScene(Scene):
    """Young's double slit — wavefronts + fringe pattern on a screen."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.wavelength = self.sim.get("wavelength_nm", 550)
        self.slit_sep = self.sim.get("slit_sep_mm", 0.5)
        self.screen_dist = self.sim.get("screen_dist_m", 1.5)

    def render(self, frame):
        t = time.time()
        src_x = int(self.W * 0.12)
        slit_x = int(self.W * 0.34)
        screen_x = int(self.W * 0.72)
        cy = int(self.H * 0.52)
        sep = 46

        # coherent source
        if "source" in self.visible or True:
            glow = frame.copy()
            cv2.circle(glow, (src_x, cy), 20, CYAN, -1)
            cv2.addWeighted(glow, 0.4, frame, 0.6, 0, frame)
            cv2.circle(frame, (src_x, cy), 8, CYAN, -1, cv2.LINE_AA)
            # incoming plane waves
            for k in range(6):
                xx = src_x + 18 + k * 16 + int((t * 30) % 16)
                if xx < slit_x - 10:
                    cv2.line(frame, (xx, cy - 40), (xx, cy + 40), (120, 160, 90), 1, cv2.LINE_AA)

        # barrier with two slits
        cv2.rectangle(frame, (slit_x - 6, cy - 200), (slit_x + 6, cy - sep - 8),
                      (150, 150, 160), -1)
        cv2.rectangle(frame, (slit_x - 6, cy - sep + 8), (slit_x + 6, cy + sep - 8),
                      (150, 150, 160), -1)
        cv2.rectangle(frame, (slit_x - 6, cy + sep + 8), (slit_x + 6, cy + 200),
                      (150, 150, 160), -1)

        # circular wavefronts from each slit
        for sy in (cy - sep, cy + sep):
            for r in range(10, 400, 26):
                rr = int((r + (t * 40) % 26))
                if rr < screen_x - slit_x + 40:
                    cv2.ellipse(frame, (slit_x, sy), (rr, rr), 0, -70, 70,
                                (90, 130, 70), 1, cv2.LINE_AA)

        # screen with fringes
        cv2.rectangle(frame, (screen_x, cy - 210), (screen_x + 12, cy + 210),
                      (60, 60, 70), -1, cv2.LINE_AA)
        for i in range(-200, 201, 2):
            phase = (i / self.slit_sep) * 0.12
            I = (math.cos(phase) ** 2)
            col = (int(255 * I), int(212 * I), 0)
            cv2.line(frame, (screen_x + 12, cy + i), (screen_x + 44, cy + i), col, 2)
        text(frame, "SCREEN", screen_x - 8, cy - 220, 0.42, TEXT, 1, FONT_S)

        fringe = self.wavelength * 1e-9 * self.screen_dist / (self.slit_sep * 1e-3) * 1000
        _panel(frame, self.W, [
            ("WAVELENGTH", f"{self.wavelength:.0f} nm", CYAN),
            ("SLIT SEP d", f"{self.slit_sep:.2f} mm", ACCENT),
            ("SCREEN D", f"{self.screen_dist:.1f} m", TEXT),
            ("FRINGE w", f"{fringe:.2f} mm", GREEN),
        ], "DOUBLE-SLIT")
        return frame


# ═══════════════════════════════ lens ══════════════════════════════
class LensScene(Scene):
    """Converging lens ray diagram with live image formation."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.f = self.sim.get("focal_cm", 12)
        self.obj_dist = self.sim.get("object_cm", 30)
        self.obj_h = self.sim.get("object_h_cm", 6)

    def render(self, frame):
        cx = int(self.W * 0.42)
        axis_y = int(self.H * 0.54)
        scale = 6  # px per cm
        t = self.elapsed()
        # object distance sweeps in if animating
        u = self.obj_dist
        if "move" in self.animations:
            u = 18 + 22 * (0.5 + 0.5 * math.sin(t * 0.5))

        f = self.f
        v = (f * u) / (u - f) if abs(u - f) > 0.1 else 9999
        mag = -v / u
        img_h = self.obj_h * mag

        # optical axis
        cv2.line(frame, (int(self.W * 0.08), axis_y), (int(self.W * 0.80), axis_y),
                 (90, 100, 115), 1, cv2.LINE_AA)
        # lens
        lens_top, lens_bot = axis_y - 90, axis_y + 90
        cv2.ellipse(frame, (cx, axis_y), (18, 90), 0, 0, 360, (120, 200, 255), 2, cv2.LINE_AA)
        ov = frame.copy()
        cv2.ellipse(ov, (cx, axis_y), (18, 90), 0, 0, 360, (120, 200, 255), -1)
        cv2.addWeighted(ov, 0.12, frame, 0.88, 0, frame)
        # focal points
        for fx in (cx - int(f * scale), cx + int(f * scale)):
            cv2.drawMarker(frame, (fx, axis_y), AMBER, cv2.MARKER_TILTED_CROSS, 10, 1)
        text(frame, "F", cx + int(f * scale) - 6, axis_y + 22, 0.4, AMBER, 1, FONT_S)
        text(frame, "F", cx - int(f * scale) - 6, axis_y + 22, 0.4, AMBER, 1, FONT_S)

        # object (arrow up)
        ox = cx - int(u * scale)
        oy = axis_y - int(self.obj_h * scale)
        cv2.arrowedLine(frame, (ox, axis_y), (ox, oy), GREEN, 3, cv2.LINE_AA, tipLength=0.2)

        # image position
        real = 0 < v < 900
        ix = cx + int(v * scale) if real else None
        iy = axis_y - int(img_h * scale) if real else None

        # three principal rays (only draw cleanly if a real image forms)
        if real:
            # ray 1: parallel to axis, then through far focal point, to image tip
            cv2.line(frame, (ox, oy), (cx, oy), CYAN, 1, cv2.LINE_AA)
            cv2.line(frame, (cx, oy), (ix, iy), CYAN, 1, cv2.LINE_AA)
            # ray 2: straight through lens centre
            cv2.line(frame, (ox, oy), (ix, iy), (120, 200, 255), 1, cv2.LINE_AA)
            # ray 3: through near focal point, then parallel
            cv2.line(frame, (ox, oy), (cx, iy), CYAN, 1, cv2.LINE_AA)
            cv2.line(frame, (cx, iy), (int(self.W * 0.78), iy), CYAN, 1, cv2.LINE_AA)
            # image arrow (inverted)
            cv2.arrowedLine(frame, (ix, axis_y), (ix, iy), RED, 3, cv2.LINE_AA, tipLength=0.2)
            chip(frame, "REAL IMAGE", ix - 30, axis_y + 20, RED, 0.38)
        else:
            # virtual image case: rays diverge, extend back dashed
            cv2.line(frame, (ox, oy), (cx, oy), CYAN, 1, cv2.LINE_AA)
            cv2.line(frame, (cx, oy), (int(self.W * 0.78), axis_y - int((oy - axis_y) * -0.4)),
                     CYAN, 1, cv2.LINE_AA)
            chip(frame, "VIRTUAL IMAGE", cx - 40, axis_y + 20, PURPLE, 0.38)

        kind = "real, inverted" if (v > 0 and u > f) else "virtual, upright"
        _panel(frame, self.W, [
            ("FOCAL f", f"{f:.0f} cm", AMBER),
            ("OBJECT u", f"{u:.0f} cm", GREEN),
            ("IMAGE v", f"{v:.0f} cm" if v < 900 else "∞", RED),
            ("MAGNIF.", f"{mag:+.2f}×", ACCENT),
            ("IMAGE", kind, MUTED),
        ], "THIN LENS")
        return frame


# ════════════════════════════ refraction ═══════════════════════════
class RefractionScene(Scene):
    """Snell's law at an interface — live bending + total internal reflection."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.n1 = self.sim.get("n1", 1.0)
        self.n2 = self.sim.get("n2", 1.5)

    def render(self, frame):
        cx = int(self.W * 0.40)
        iy = int(self.H * 0.5)
        t = self.elapsed()
        theta_i = math.radians(20 + 45 * (0.5 + 0.5 * math.sin(t * 0.4))) \
            if "sweep" in self.animations else math.radians(35)

        # two media
        top = frame.copy()
        cv2.rectangle(top, (0, 0), (self.W, iy), (120, 90, 40), -1)
        cv2.addWeighted(top, 0.10, frame, 0.90, 0, frame)
        bot = frame.copy()
        cv2.rectangle(bot, (0, iy), (self.W, self.H), (150, 120, 60), -1)
        cv2.addWeighted(bot, 0.16, frame, 0.84, 0, frame)
        cv2.line(frame, (0, iy), (self.W, iy), (180, 190, 210), 2, cv2.LINE_AA)
        # normal
        for yy in range(iy - 150, iy + 150, 10):
            cv2.line(frame, (cx, yy), (cx, yy + 5), (100, 110, 125), 1)

        # incident ray
        L = 210
        ix = int(cx - math.sin(theta_i) * L)
        iyy = int(iy - math.cos(theta_i) * L)
        glow = frame.copy()
        cv2.line(glow, (ix, iyy), (cx, iy), CYAN, 6, cv2.LINE_AA)
        cv2.addWeighted(glow, 0.3, frame, 0.7, 0, frame)
        cv2.line(frame, (ix, iyy), (cx, iy), CYAN, 2, cv2.LINE_AA)

        # refraction / TIR
        sin_t = self.n1 * math.sin(theta_i) / self.n2
        tir = sin_t > 1.0
        if tir:
            rx = int(cx + math.sin(theta_i) * L)
            ryy = int(iy - math.cos(theta_i) * L)
            cv2.line(frame, (cx, iy), (rx, ryy), RED, 2, cv2.LINE_AA)
            chip(frame, "TOTAL INTERNAL REFLECTION", cx + 20, iy - 40, RED, 0.4)
            theta_r = None
        else:
            theta_r = math.asin(sin_t)
            tx = int(cx + math.sin(theta_r) * L)
            tyy = int(iy + math.cos(theta_r) * L)
            cv2.line(frame, (cx, iy), (tx, tyy), AMBER, 2, cv2.LINE_AA)
            # faint partial reflection
            rx = int(cx + math.sin(theta_i) * L * 0.6)
            ryy = int(iy - math.cos(theta_i) * L * 0.6)
            cv2.line(frame, (cx, iy), (rx, ryy), (100, 100, 120), 1, cv2.LINE_AA)

        crit = math.degrees(math.asin(self.n2 / self.n1)) if self.n1 > self.n2 else None
        rows = [("n1 (top)", f"{self.n1:.2f}", ACCENT),
                ("n2 (bottom)", f"{self.n2:.2f}", AMBER),
                ("INCIDENT θ", f"{math.degrees(theta_i):.0f}°", CYAN),
                ("REFRACTED θ", f"{math.degrees(theta_r):.0f}°" if theta_r else "—", AMBER)]
        _panel(frame, self.W, rows, "SNELL'S LAW")
        return frame


# ═══════════════════════════════ motor ═════════════════════════════
class MotorScene(Scene):
    """DC motor — magnetic field, current loop, force F = BIL, rotation."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.B = self.sim.get("field_T", 0.4)
        self.I = self.sim.get("current_A", 2.0)
        self.L = self.sim.get("loop_len_m", 0.1)
        self.angle = 0.0
        self.last = None

    def render(self, frame):
        cx, cy = int(self.W * 0.38), int(self.H * 0.52)
        now = time.time()
        if self.last is None:
            self.last = now
        dt = min(now - self.last, 0.05); self.last = now
        spinning = "run" in self.animations
        if spinning:
            self.angle += dt * 3.0

        # magnet poles N (left) S (right)
        cv2.rectangle(frame, (cx - 230, cy - 110), (cx - 170, cy + 110), (60, 80, 200), -1, cv2.LINE_AA)
        cv2.rectangle(frame, (cx + 170, cy - 110), (cx + 230, cy + 110), (200, 70, 70), -1, cv2.LINE_AA)
        text(frame, "N", cx - 208, cy + 8, 0.9, TEXT, 2)
        text(frame, "S", cx + 190, cy + 8, 0.9, TEXT, 2)

        # field lines N -> S
        for k in range(-2, 3):
            yy = cy + k * 44
            cv2.arrowedLine(frame, (cx - 165, yy), (cx + 165, yy),
                            (90, 110, 150), 1, cv2.LINE_AA, tipLength=0.03)

        # rotating current loop (drawn as rectangle rotated about vertical axis)
        w = 120 * math.cos(self.angle)
        loop = np.array([(cx - int(w), cy - 70), (cx + int(w), cy - 70),
                         (cx + int(w), cy + 70), (cx - int(w), cy + 70)], np.int32)
        glow = frame.copy()
        cv2.polylines(glow, [loop], True, ACCENT, 6, cv2.LINE_AA)
        cv2.addWeighted(glow, 0.3, frame, 0.7, 0, frame)
        cv2.polylines(frame, [loop], True, CYAN, 3, cv2.LINE_AA)

        # current-direction dots/crosses on the two vertical sides
        left_x = cx - int(w)
        right_x = cx + int(w)
        cv2.circle(frame, (left_x, cy), 8, GREEN, 2, cv2.LINE_AA)
        cv2.circle(frame, (left_x, cy), 2, GREEN, -1, cv2.LINE_AA)  # dot = out
        cv2.line(frame, (right_x - 6, cy - 6), (right_x + 6, cy + 6), RED, 2, cv2.LINE_AA)
        cv2.line(frame, (right_x - 6, cy + 6), (right_x + 6, cy - 6), RED, 2, cv2.LINE_AA)  # cross = in

        # force arrows (F = BIL), opposite on each side -> torque
        F = self.B * self.I * self.L * 100
        cv2.arrowedLine(frame, (left_x, cy), (left_x, cy - int(F)), AMBER, 3, cv2.LINE_AA, tipLength=0.3)
        cv2.arrowedLine(frame, (right_x, cy), (right_x, cy + int(F)), AMBER, 3, cv2.LINE_AA, tipLength=0.3)

        # commutator + axle
        cv2.circle(frame, (cx, cy), 10, (150, 150, 160), -1, cv2.LINE_AA)

        force = self.B * self.I * self.L
        rpm = self.angle / (2 * math.pi) / max(self.elapsed(), 0.1) * 60 if spinning else 0
        _panel(frame, self.W, [
            ("FIELD B", f"{self.B:.2f} T", HOT),
            ("CURRENT I", f"{self.I:.1f} A", GREEN),
            ("LENGTH L", f"{self.L*100:.0f} cm", TEXT),
            ("FORCE BIL", f"{force:.3f} N", AMBER),
            ("STATE", "SPINNING" if spinning else "static", ACCENT if spinning else MUTED),
        ], "DC MOTOR")
        return frame


# ════════════════════════════ induction ════════════════════════════
class InductionScene(Scene):
    """Faraday's law — magnet moving through a coil induces EMF on a galvanometer."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.N = self.sim.get("turns", 200)
        self.pos = -1.0
        self.last = None

    def render(self, frame):
        cx, cy = int(self.W * 0.38), int(self.H * 0.5)
        now = time.time()
        if self.last is None: self.last = now
        dt = min(now - self.last, 0.05); self.last = now
        moving = "move" in self.animations
        # magnet oscillates through the coil
        v = 0.0
        if moving:
            self.pos = math.sin(self.elapsed() * 1.4)
            v = math.cos(self.elapsed() * 1.4) * 1.4

        # coil (series of ellipses)
        coil_x = cx
        for i in range(8):
            ex = coil_x - 70 + i * 20
            cv2.ellipse(frame, (ex, cy), (14, 50), 0, -90, 90, (200, 170, 90), 2, cv2.LINE_AA)
            cv2.ellipse(frame, (ex + 10, cy), (14, 50), 0, 90, 270, (170, 140, 70), 2, cv2.LINE_AA)

        # magnet
        mx = int(cx + self.pos * 260)
        cv2.rectangle(frame, (mx - 40, cy - 18), (mx, cy + 18), (60, 80, 200), -1, cv2.LINE_AA)
        cv2.rectangle(frame, (mx, cy - 18), (mx + 40, cy + 18), (200, 70, 70), -1, cv2.LINE_AA)
        text(frame, "N", mx - 30, cy + 6, 0.6, TEXT, 1); text(frame, "S", mx + 14, cy + 6, 0.6, TEXT, 1)
        if moving:
            cv2.arrowedLine(frame, (mx, cy - 40), (mx + int(v * 40), cy - 40), GREEN, 2, cv2.LINE_AA, tipLength=0.3)

        # EMF proportional to velocity when magnet near coil
        near = math.exp(-((mx - cx) / 120.0) ** 2)
        emf = -self.N * v * near * 0.02

        # wires to galvanometer
        gx, gy = cx, cy + 180
        cv2.line(frame, (coil_x - 60, cy + 50), (gx - 60, gy - 40), (150, 160, 180), 2, cv2.LINE_AA)
        cv2.line(frame, (coil_x + 90, cy + 50), (gx + 60, gy - 40), (150, 160, 180), 2, cv2.LINE_AA)
        # galvanometer dial
        glass_panel(frame, gx - 70, gy - 40, 140, 90, radius=12, border=ACCENT)
        text(frame, "GALVANOMETER", gx - 60, gy - 22, 0.38, ACCENT, 1, FONT_S)
        ncx, ncy = gx, gy + 30
        cv2.ellipse(frame, (ncx, ncy), (50, 50), 0, 180, 360, (90, 100, 115), 1, cv2.LINE_AA)
        ang = math.radians(90 - max(-80, min(80, emf * 400)))
        nx = int(ncx + math.cos(ang) * 42); ny = int(ncy - math.sin(ang) * 42)
        col = GREEN if abs(emf) > 0.001 else MUTED
        cv2.line(frame, (ncx, ncy), (nx, ny), col, 2, cv2.LINE_AA)
        cv2.circle(frame, (ncx, ncy), 4, col, -1, cv2.LINE_AA)
        text(frame, "0", ncx - 4, ncy - 30, 0.36, MUTED, 1, FONT_S, shadow=False)
        text(frame, "-", ncx - 44, ncy + 4, 0.4, MUTED, 1, FONT_S, shadow=False)
        text(frame, "+", ncx + 40, ncy + 4, 0.4, MUTED, 1, FONT_S, shadow=False)

        _panel(frame, self.W, [
            ("COIL TURNS", f"{self.N}", TEXT),
            ("MAGNET v", f"{v:+.2f} m/s", GREEN),
            ("FLUX LINK", f"{near*100:.0f}%", ACCENT),
            ("INDUCED EMF", f"{emf*1000:+.1f} mV", RED if abs(emf) > 0.001 else MUTED),
            ("LENZ", "opposes Δflux", PURPLE),
        ], "FARADAY INDUCTION")
        return frame


# ═══════════════════════════ photoelectric ═════════════════════════
class PhotoelectricScene(Scene):
    """Photoelectric effect — photons eject electrons above threshold frequency."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.work_fn = self.sim.get("work_function_eV", 2.3)
        self.freq = self.sim.get("freq_PHz", 0.8)   # 10^15 Hz
        self.electrons = []
        self.rng = np.random.default_rng(4)

    def render(self, frame):
        cx = int(self.W * 0.40); cy = int(self.H * 0.5)
        t = self.elapsed()
        h_eV = 4.1357e-15 * (self.freq * 1e15)      # photon energy eV
        ke = h_eV - self.work_fn
        emits = ke > 0 and "illuminate" in self.animations

        # metal plate (cathode)
        cv2.rectangle(frame, (cx - 200, cy - 90), (cx - 170, cy + 90), (150, 150, 165), -1, cv2.LINE_AA)
        text(frame, "METAL", cx - 210, cy + 120, 0.4, TEXT, 1, FONT_S)
        # collector (anode)
        cv2.rectangle(frame, (cx + 170, cy - 90), (cx + 200, cy + 90), (120, 120, 140), -1, cv2.LINE_AA)
        text(frame, "COLLECTOR", cx + 130, cy + 120, 0.4, TEXT, 1, FONT_S)

        # incoming photons (wavy) — colour by frequency
        pcol = (int(255 * min(self.freq, 1)), int(120), int(255 * (1 - min(self.freq, 1)) + 100))
        if "illuminate" in self.animations:
            for k in range(5):
                px = int(self.W * 0.08 + ((t * 260 + k * 70) % (cx - 170 - self.W * 0.08)))
                py = cy - 50 + k * 25
                for s in range(6):
                    x1 = px + s * 6
                    y1 = py + int(math.sin(s * 1.2 + t * 8) * 5)
                    cv2.circle(frame, (x1, y1), 2, pcol, -1, cv2.LINE_AA)

        # ejected electrons
        if emits:
            if self.rng.random() < 0.3:
                self.electrons.append([cx - 168, cy + self.rng.integers(-70, 70),
                                       2 + ke * 1.5])
        alive = []
        for e in self.electrons:
            e[0] += e[2]
            if e[0] < cx + 168:
                cv2.circle(frame, (int(e[0]), int(e[1])), 4, ACCENT, -1, cv2.LINE_AA)
                cv2.circle(frame, (int(e[0]), int(e[1])), 7, (255, 200, 100), 1, cv2.LINE_AA)
                alive.append(e)
        self.electrons = alive[-40:]

        # verdict chip
        if "illuminate" in self.animations:
            if emits:
                chip(frame, f"ELECTRONS EJECTED  KE={ke:.2f} eV", cx - 110, cy - 130, GREEN, 0.42)
            else:
                chip(frame, "NO EMISSION — below threshold", cx - 110, cy - 130, RED, 0.42)

        f0 = self.work_fn / 4.1357     # threshold freq in PHz
        _panel(frame, self.W, [
            ("WORK FN φ", f"{self.work_fn:.2f} eV", AMBER),
            ("FREQUENCY", f"{self.freq:.2f} PHz", pcol),
            ("PHOTON E", f"{h_eV:.2f} eV", CYAN),
            ("MAX KE", f"{max(ke,0):.2f} eV", GREEN if ke > 0 else RED),
            ("THRESHOLD f0", f"{f0:.2f} PHz", PURPLE),
        ], "PHOTOELECTRIC")
        return frame


# ═══════════════════════════════ Bohr ══════════════════════════════
class BohrScene(Scene):
    """Hydrogen Bohr model — electron orbits, energy-level jumps, photon emission."""

    LEVELS = [-13.6, -3.4, -1.51, -0.85, -0.54]

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.phase = 0.0
        self.photons = []

    def render(self, frame):
        cx, cy = int(self.W * 0.34), int(self.H * 0.52)
        t = self.elapsed()
        # nucleus
        glow = frame.copy(); cv2.circle(glow, (cx, cy), 20, RED, -1)
        cv2.addWeighted(glow, 0.4, frame, 0.6, 0, frame)
        cv2.circle(frame, (cx, cy), 9, (80, 90, 240), -1, cv2.LINE_AA)

        # orbits
        radii = [50, 90, 135, 185, 240]
        for i, r in enumerate(radii):
            cv2.circle(frame, (cx, cy), r, (70, 80, 100), 1, cv2.LINE_AA)
            text(frame, f"n={i+1}", cx + r - 20, cy - 6, 0.36, MUTED, 1, FONT_S, shadow=False)

        # animated electron jump n=3 -> n=1 emitting a photon
        cycle = 4.0
        ph = (t % cycle) / cycle
        if ph < 0.5:
            n_from = 3; level_r = radii[2]
        else:
            n_from = 1; level_r = radii[0]
            if 0.5 <= ph < 0.54 and "excite" in self.animations:
                self.photons.append([cx, cy, t])
        ang = t * 3
        ex = int(cx + level_r * math.cos(ang)); ey = int(cy + level_r * math.sin(ang))
        cv2.circle(frame, (ex, ey), 8, ACCENT, -1, cv2.LINE_AA)
        cv2.circle(frame, (ex, ey), 12, (255, 220, 120), 1, cv2.LINE_AA)

        # emitted photons flying out
        alive = []
        for p in self.photons:
            age = t - p[2]
            if age < 1.5:
                px = int(p[0] + math.cos(age * 6) * age * 200)
                py = int(p[1] + age * 160)
                for s in range(5):
                    cv2.circle(frame, (px + s * 5, py + int(math.sin(s + age * 10) * 4)),
                               2, (120, 200, 255), -1, cv2.LINE_AA)
                alive.append(p)
        self.photons = alive

        # energy-level diagram on the right of the scene
        dx = int(self.W * 0.56); dtop = int(self.H * 0.24); dh = int(self.H * 0.5)
        cv2.line(frame, (dx, dtop), (dx, dtop + dh), (90, 100, 115), 1, cv2.LINE_AA)
        for i, E in enumerate(self.LEVELS):
            yy = int(dtop + dh * (1 - (E + 13.6) / 13.6))
            cv2.line(frame, (dx, yy), (dx + 130, yy), (120, 140, 170), 1, cv2.LINE_AA)
            text(frame, f"n={i+1}  {E:.2f} eV", dx + 8, yy - 4, 0.36, TEXT, 1, FONT_S, shadow=False)
        # transition arrow 3->1
        y3 = int(dtop + dh * (1 - (self.LEVELS[2] + 13.6) / 13.6))
        y1 = int(dtop + dh * (1 - (self.LEVELS[0] + 13.6) / 13.6))
        cv2.arrowedLine(frame, (dx + 70, y3), (dx + 70, y1), ACCENT, 2, cv2.LINE_AA, tipLength=0.08)
        dE = self.LEVELS[2] - self.LEVELS[0]
        text(frame, f"ΔE={abs(dE):.2f} eV", dx + 78, (y3 + y1) // 2, 0.36, ACCENT, 1, FONT_S)

        _panel(frame, self.W, [
            ("GROUND", "-13.6 eV", PURPLE),
            ("JUMP", "n=3 → n=1", ACCENT),
            ("ΔE", f"{abs(dE):.2f} eV", AMBER),
            ("PHOTON λ", f"{1240/abs(dE):.0f} nm", CYAN),
        ], "BOHR MODEL")
        return frame
