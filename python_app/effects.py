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
