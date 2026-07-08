# python_app/effects.py
"""
CircuitVerse v2 — animated AR effects.
Current-flow particles, glowing wires, LED glow halos, marker lock ring.
"""

import time
import math
import cv2
import numpy as np

from hud import ACCENT, GREEN, AMBER, RED


class CurrentFlow:
    """Particles travelling along every wire, speed ∝ current."""

    def __init__(self):
        self.t0 = time.time()

    def draw(self, frame, wires, current_amps):
        """wires: list of ((x1,y1),(x2,y2)). current_amps: loop current."""
        if current_amps <= 0:
            return
        t = time.time() - self.t0
        speed = min(0.25 + current_amps * 40.0, 1.4)      # cycles / s
        n_particles = 3
        for (p1, p2) in wires:
            length = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            if length < 8:
                continue
            for k in range(n_particles):
                u = ((t * speed) + k / n_particles) % 1.0
                x = int(p1[0] + (p2[0] - p1[0]) * u)
                y = int(p1[1] + (p2[1] - p1[1]) * u)
                cv2.circle(frame, (x, y), 3, (120, 255, 170), -1, cv2.LINE_AA)
                cv2.circle(frame, (x, y), 6, (60, 200, 90), 1, cv2.LINE_AA)


def glow_wire(frame, p1, p2, color=GREEN, active=True):
    """Wire drawn as dark base + bright core + soft outer glow."""
    if active:
        overlay = frame.copy()
        cv2.line(overlay, p1, p2, color, 9, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
    cv2.line(frame, p1, p2, (30, 60, 30), 5, cv2.LINE_AA)
    cv2.line(frame, p1, p2, color if active else (70, 90, 70), 2, cv2.LINE_AA)


def led_glow(frame, x, y, status: str):
    """Pulsing halo behind an LED based on solver status."""
    if status.startswith("OFF"):
        return
    color = RED if "OVER" in status else (80, 200, 255)   # warm LED yellow-white
    pulse = 0.55 + 0.45 * math.sin(time.time() * 5.0)
    r = int(34 + 10 * pulse)
    overlay = frame.copy()
    cv2.circle(overlay, (x, y), r, color, -1, cv2.LINE_AA)
    cv2.circle(overlay, (x, y), r + 14, color, 2, cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.28 * pulse + 0.12, frame, 1 - (0.28 * pulse + 0.12), 0, frame)


def marker_lock(frame, corners, exp_name):
    """Sci-fi lock ring around the detected ArUco marker."""
    pts = corners.reshape(-1, 2).astype(int)
    cx, cy = pts.mean(axis=0).astype(int)
    radius = int(np.linalg.norm(pts[0] - pts[2]) / 2) + 16
    spin = (time.time() * 90) % 360
    for a0 in (0, 90, 180, 270):
        cv2.ellipse(frame, (cx, cy), (radius, radius),
                    spin + a0, 0, 60, ACCENT, 2, cv2.LINE_AA)
    cv2.polylines(frame, [pts], True, ACCENT, 1, cv2.LINE_AA)


def scanline(frame, t):
    """Subtle animated scanline sweep for ambient sci-fi feel (very light)."""
    H, W = frame.shape[:2]
    y = int((t * 60) % (H + 120)) - 60
    if 0 <= y < H:
        overlay = frame.copy()
        cv2.line(overlay, (0, y), (W, y), (200, 180, 120), 1)
        cv2.addWeighted(overlay, 0.08, frame, 0.92, 0, frame)


def vignette(frame, strength=0.35):
    """Cached radial vignette for cinematic depth."""
    H, W = frame.shape[:2]
    key = (H, W, strength)
    if getattr(vignette, "_key", None) != key:
        kx = cv2.getGaussianKernel(W, W * 0.7)
        ky = cv2.getGaussianKernel(H, H * 0.7)
        m = ky @ kx.T
        m = (m / m.max())
        vignette._mask = (1 - strength) + strength * m[..., None]
        vignette._key = key
    np.multiply(frame, vignette._mask, out=frame, casting="unsafe")


class Ambient:
    """Cinematic floating dust/energy motes drifting across the whole frame."""

    def __init__(self, n=60, seed=7):
        self.rng = np.random.default_rng(seed)
        self.p = None
        self.n = n

    def _init(self, W, H):
        self.p = np.zeros((self.n, 4), np.float32)     # x, y, speed, size
        self.p[:, 0] = self.rng.uniform(0, W, self.n)
        self.p[:, 1] = self.rng.uniform(0, H, self.n)
        self.p[:, 2] = self.rng.uniform(6, 26, self.n)
        self.p[:, 3] = self.rng.uniform(0.6, 2.2, self.n)

    def draw(self, frame, tint=(255, 200, 120)):
        H, W = frame.shape[:2]
        if self.p is None:
            self._init(W, H)
        t = time.time()
        overlay = frame.copy()
        for i in range(self.n):
            x, y, sp, sz = self.p[i]
            y -= sp * 0.016
            x += math.sin(t * 0.5 + i) * 0.4
            if y < -4:
                y = H + 4
                x = self.rng.uniform(0, W)
            self.p[i, 0], self.p[i, 1] = x, y
            a = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 1.5 + i))
            col = tuple(int(c * a) for c in tint)
            cv2.circle(overlay, (int(x), int(y)), int(sz), col, -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.10, frame, 0.90, 0, frame)


def bloom(frame, strength=0.18, thresh=205):
    """Cheap bloom: blur the bright regions and add them back."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)
    bright = cv2.bitwise_and(frame, frame, mask=mask)
    bright = cv2.GaussianBlur(bright, (0, 0), 9)
    cv2.addWeighted(frame, 1.0, bright, strength, 0, frame)


def corner_flourish(frame, t):
    """Animated HUD corner brackets — subtle sci-fi framing."""
    H, W = frame.shape[:2]
    from hud import ACCENT
    L = 46
    a = 0.4 + 0.25 * math.sin(t * 2)
    col = tuple(int(c * a) for c in ACCENT)
    ov = frame.copy()
    for (cx, cy, dx, dy) in [(8, 8, 1, 1), (W - 8, 8, -1, 1),
                             (8, H - 8, 1, -1), (W - 8, H - 8, -1, -1)]:
        cv2.line(ov, (cx, cy), (cx + dx * L, cy), col, 2, cv2.LINE_AA)
        cv2.line(ov, (cx, cy), (cx, cy + dy * L), col, 2, cv2.LINE_AA)
    cv2.addWeighted(ov, 0.5, frame, 0.5, 0, frame)
