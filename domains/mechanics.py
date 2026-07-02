# domains/mechanics.py
"""
Mechanics scenes:
  PendulumScene   — simple pendulum, real small-angle + energy exchange,
                    live θ(t), velocity, KE/PE bars
  ProjectileScene — projectile motion, live trajectory trace, velocity
                    vectors, range/apex readout
"""

import math
import time
import cv2
import numpy as np

from hud import (ACCENT, PURPLE, GREEN, AMBER, RED, TEXT, MUTED,
                 glass_panel, text, text_size, chip, FONT_S)
from . import Scene

G = 9.81


# ══════════════════════════════ pendulum ═══════════════════════════
class PendulumScene(Scene):
    """Simple pendulum. Uses the full nonlinear solution via small time steps."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.L = self.sim.get("length_m", 1.2)          # metres
        self.theta0 = math.radians(self.sim.get("angle_deg", 35))
        self.mass = self.sim.get("mass_kg", 0.5)
        self.theta = self.theta0
        self.omega = 0.0
        self.last = None
        self.trail = []

    def _integrate(self):
        now = time.time()
        if self.last is None:
            self.last = now
            return
        dt = min(now - self.last, 0.05)
        self.last = now
        if "swing" not in self.animations:
            return
        # semi-implicit Euler on θ'' = −(g/L) sinθ
        self.omega += -(G / self.L) * math.sin(self.theta) * dt
        self.omega *= 0.999  # tiny damping
        self.theta += self.omega * dt

    def render(self, frame):
        self._integrate()
        px = int(self.W * 0.40)
        py = int(self.H * 0.24)
        scale = 260 / self.L   # px per metre

        bob_x = int(px + math.sin(self.theta) * self.L * scale)
        bob_y = int(py + math.cos(self.theta) * self.L * scale)

        # pivot mount
        cv2.line(frame, (px - 70, py), (px + 70, py), (150, 150, 160), 4, cv2.LINE_AA)
        cv2.circle(frame, (px, py), 6, (200, 200, 210), -1, cv2.LINE_AA)

        # arc guide
        cv2.ellipse(frame, (px, py), (int(self.L * scale), int(self.L * scale)),
                    0, 60, 120, (70, 80, 95), 1, cv2.LINE_AA)

        # trail
        if "swing" in self.animations:
            self.trail.append((bob_x, bob_y))
            self.trail = self.trail[-40:]
        for i, (tx, ty) in enumerate(self.trail):
            a = i / max(len(self.trail), 1)
            cv2.circle(frame, (tx, ty), 2, (int(120 * a), int(200 * a), int(120 * a)), -1, cv2.LINE_AA)

        # string + bob
        cv2.line(frame, (px, py), (bob_x, bob_y), (210, 210, 220), 2, cv2.LINE_AA)
        glow = frame.copy()
        cv2.circle(glow, (bob_x, bob_y), 26, AMBER, -1)
        cv2.addWeighted(glow, 0.25, frame, 0.75, 0, frame)
        cv2.circle(frame, (bob_x, bob_y), 18, (40, 120, 220), -1, cv2.LINE_AA)
        cv2.circle(frame, (bob_x, bob_y), 18, AMBER, 2, cv2.LINE_AA)

        # velocity vector
        v = self.omega * self.L                       # linear speed (m/s)
        if abs(v) > 0.05:
            vx = int(bob_x + math.cos(self.theta) * v * 26)
            vy = int(bob_y - math.sin(self.theta) * v * 26)
            cv2.arrowedLine(frame, (bob_x, bob_y), (vx, vy), GREEN, 2, cv2.LINE_AA, tipLength=0.3)

        self._readout(frame, v)
        return frame

    def _readout(self, frame, v):
        h = self.L * (1 - math.cos(self.theta))       # height above lowest point
        pe = self.mass * G * h
        ke = 0.5 * self.mass * v * v
        total = pe + ke if (pe + ke) > 1e-6 else 1e-6
        T = 2 * math.pi * math.sqrt(self.L / G)        # small-angle period

        x0, y0 = self.W - 264, 92
        rows = [("LENGTH", f"{self.L:.2f} m", TEXT),
                ("ANGLE theta", f"{math.degrees(self.theta):+.1f} deg", ACCENT),
                ("SPEED", f"{abs(v):.2f} m/s", GREEN),
                ("PERIOD T", f"{T:.2f} s", PURPLE)]
        panel_h = 132 + 30 * len(rows)
        glass_panel(frame, x0, y0, 248, panel_h, radius=16, border=ACCENT)
        text(frame, "PENDULUM PHYSICS", x0 + 16, y0 + 28, 0.5, ACCENT, 1, FONT_S)
        cv2.line(frame, (x0 + 16, y0 + 38), (x0 + 232, y0 + 38), (70, 60, 45), 1)
        for i, (k, val, col) in enumerate(rows):
            yy = y0 + 64 + i * 30
            text(frame, k, x0 + 16, yy, 0.44, MUTED, 1, FONT_S)
            vw, _ = text_size(val, 0.48, 1, FONT_S)
            text(frame, val, x0 + 232 - vw, yy, 0.48, col, 1, FONT_S)
        # energy bars
        by = y0 + 64 + len(rows) * 30 + 6
        self._bar(frame, x0 + 16, by, 216, ke / total, GREEN, "KE")
        self._bar(frame, x0 + 16, by + 30, 216, pe / total, AMBER, "PE")

    def _bar(self, frame, x, y, w, frac, col, label):
        text(frame, label, x, y + 10, 0.4, MUTED, 1, FONT_S)
        bx = x + 30
        bw = w - 30
        overlay = frame.copy()
        cv2.rectangle(overlay, (bx, y), (bx + bw, y + 12), (60, 55, 45), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        cv2.rectangle(frame, (bx, y), (bx + int(bw * frac), y + 12), col, -1, cv2.LINE_AA)


# ══════════════════════════════ projectile ═════════════════════════
class ProjectileScene(Scene):
    """Projectile motion with live trajectory and vector decomposition."""

    def __init__(self, raw, W, H):
        super().__init__(raw, W, H)
        self.v0 = self.sim.get("velocity_ms", 22.0)
        self.angle = math.radians(self.sim.get("angle_deg", 55))
        self.flight = 2 * self.v0 * math.sin(self.angle) / G
        self.range_m = self.v0 * math.cos(self.angle) * self.flight
        self.apex = (self.v0 * math.sin(self.angle)) ** 2 / (2 * G)

    def render(self, frame):
        gx0 = int(self.W * 0.10)
        gy0 = int(self.H * 0.82)
        scale = min((self.W * 0.62) / max(self.range_m, 1),
                    (self.H * 0.5) / max(self.apex, 1))

        # ground
        cv2.line(frame, (gx0, gy0), (int(self.W * 0.80), gy0), (150, 150, 160), 3, cv2.LINE_AA)
        # launch pad
        cv2.rectangle(frame, (gx0 - 12, gy0 - 8), (gx0 + 12, gy0), AMBER, -1, cv2.LINE_AA)

        running = "launch" in self.animations
        t_now = min(self.elapsed(), self.flight) if running else 0.0

        # full faint arc
        full = []
        for i in range(101):
            t = self.flight * i / 100
            x = self.v0 * math.cos(self.angle) * t
            y = self.v0 * math.sin(self.angle) * t - 0.5 * G * t * t
            full.append((int(gx0 + x * scale), int(gy0 - y * scale)))
        cv2.polylines(frame, [np.array(full, np.int32)], False, (70, 80, 95), 1, cv2.LINE_AA)

        # traced arc so far
        traced = []
        for i in range(int(100 * t_now / self.flight) + 1) if self.flight > 0 else []:
            t = self.flight * i / 100
            x = self.v0 * math.cos(self.angle) * t
            y = self.v0 * math.sin(self.angle) * t - 0.5 * G * t * t
            traced.append((int(gx0 + x * scale), int(gy0 - y * scale)))
        if len(traced) > 1:
            cv2.polylines(frame, [np.array(traced, np.int32)], False, ACCENT, 2, cv2.LINE_AA)

        # projectile + velocity vectors
        x = self.v0 * math.cos(self.angle) * t_now
        y = self.v0 * math.sin(self.angle) * t_now - 0.5 * G * t_now * t_now
        vx = self.v0 * math.cos(self.angle)
        vy = self.v0 * math.sin(self.angle) - G * t_now
        bx, by = int(gx0 + x * scale), int(gy0 - y * scale)
        glow = frame.copy()
        cv2.circle(glow, (bx, by), 18, ACCENT, -1)
        cv2.addWeighted(glow, 0.3, frame, 0.7, 0, frame)
        cv2.circle(frame, (bx, by), 10, (40, 160, 240), -1, cv2.LINE_AA)
        cv2.circle(frame, (bx, by), 10, ACCENT, 2, cv2.LINE_AA)
        if running and t_now < self.flight:
            cv2.arrowedLine(frame, (bx, by), (int(bx + vx * 6), by), GREEN, 2, cv2.LINE_AA, tipLength=0.3)
            cv2.arrowedLine(frame, (bx, by), (bx, int(by - vy * 6)), RED, 2, cv2.LINE_AA, tipLength=0.3)
            cv2.arrowedLine(frame, (bx, by), (int(bx + vx * 6), int(by - vy * 6)),
                            AMBER, 2, cv2.LINE_AA, tipLength=0.25)

        # apex marker
        apex_x = int(gx0 + (self.range_m / 2) * scale)
        apex_y = int(gy0 - self.apex * scale)
        cv2.drawMarker(frame, (apex_x, apex_y), PURPLE, cv2.MARKER_TRIANGLE_UP, 12, 2)
        chip(frame, f"apex {self.apex:.1f} m", apex_x - 30, apex_y - 34, PURPLE, 0.4)

        self._readout(frame, t_now, vx, vy, x, y)
        return frame

    def _readout(self, frame, t, vx, vy, x, y):
        speed = math.hypot(vx, vy)
        x0, y0 = self.W - 264, 92
        rows = [("LAUNCH v0", f"{self.v0:.0f} m/s", TEXT),
                ("ANGLE", f"{math.degrees(self.angle):.0f} deg", ACCENT),
                ("TIME", f"{t:.2f} s", GREEN),
                ("HEIGHT", f"{max(y,0):.1f} m", AMBER),
                ("SPEED", f"{speed:.1f} m/s", GREEN),
                ("RANGE", f"{self.range_m:.1f} m", PURPLE)]
        glass_panel(frame, x0, y0, 248, 58 + 30 * len(rows), radius=16, border=ACCENT)
        text(frame, "PROJECTILE MOTION", x0 + 16, y0 + 28, 0.5, ACCENT, 1, FONT_S)
        cv2.line(frame, (x0 + 16, y0 + 38), (x0 + 232, y0 + 38), (70, 60, 45), 1)
        for i, (k, val, col) in enumerate(rows):
            yy = y0 + 64 + i * 30
            text(frame, k, x0 + 16, yy, 0.44, MUTED, 1, FONT_S)
            vw, _ = text_size(val, 0.48, 1, FONT_S)
            text(frame, val, x0 + 232 - vw, yy, 0.48, col, 1, FONT_S)
