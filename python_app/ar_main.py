# python_app/ar_main.py
"""
==================================================================
  CircuitVerse v2.0 - AR Science Laboratory
  Anshul Pagar - SRM Institute of Science and Technology

  M menu | N next | B back | R reset | SPACE autoplay | F fullscreen | Q quit
==================================================================
"""

import sys
import os
import json
import time
import math
from pathlib import Path

import numpy as np
import cv2
import cv2.aruco as aruco

# ── path fix ──────────────────────────────────────────────────────
APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
for p in (str(ROOT_DIR), str(APP_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from circuit_engine.loader import load_experiment
from circuit_engine.solver import solve, rc_voltage_at

import hud
import effects
from domains import create_scene
from menu import ExperimentMenu

# ── catalog: subject → [(marker_id, display_name), ...] for the menu ──
EXPERIMENT_CATALOG = {
    "Physics": [
        (0, "Simple Harmonic Motion"),
        (1, "Resonance & Driven Oscillation"),
        (2, "Young's Double-Slit"),
        (3, "Converging Lens"),
        (4, "Refraction & TIR"),
        (5, "DC Motor (F = BIL)"),
        (6, "Electromagnetic Induction"),
        (7, "Photoelectric Effect"),
        (8, "Bohr Model & Spectra"),
    ],
    "Chemistry": [
        (9,  "Acid-Base Titration"),
        (10, "Electrolysis of Water"),
        (11, "Flame Test — Metal Ions"),
        (12, "Reaction Rate & Collisions"),
    ],
    "Biology": [
        (13, "Animal Cell Anatomy"),
        (14, "DNA Replication"),
        (15, "Neuron — Action Potential"),
        (16, "Photosynthesis"),
    ],
    "Circuits": [
        (17, "Ohm's Law (A + V meters)"),
        (18, "Series — Voltage Division"),
        (19, "Parallel — Current Division"),
        (20, "Wheatstone Bridge"),
    ],
}
from hud import (ACCENT, PURPLE, GREEN, AMBER, RED, TEXT, MUTED,
                 glass_panel, text, text_size, chip, progress_bar, wrap_text,
                 value_tag, rc_graph)

# ══════════════════════════════ config ════════════════════════════
ASSETS_DIR = ROOT_DIR / "assets"
EXPERIMENTS_DIR = ROOT_DIR / "experiments"

EXPERIMENT_FILES = {
    # ── Physics (markers 0–8) ──
    0: "phy1_shm.json",
    1: "phy2_resonance.json",
    2: "phy3_interference.json",
    3: "phy4_lens.json",
    4: "phy5_refraction.json",
    5: "phy6_motor.json",
    6: "phy7_induction.json",
    7: "phy8_photoelectric.json",
    8: "phy9_bohr.json",
    # ── Chemistry (markers 9–12) ──
    9:  "exp9_chem_titration.json",
    10: "exp10_chem_electrolysis.json",
    11: "chem3_flame.json",
    12: "chem4_rate.json",
    # ── Biology (markers 13–16) ──
    13: "exp11_bio_cell.json",
    14: "exp12_bio_dna.json",
    15: "bio3_neuron.json",
    16: "bio4_photosynthesis.json",
    # ── Circuits (markers 17–20) ──
    17: "cir1_ohms.json",
    18: "cir2_series.json",
    19: "cir3_parallel.json",
    20: "cir4_wheatstone.json",
}

DOMAIN_ACCENT = {
    "electronics": None,      # uses default cyan
    "physics":     (255, 170, 60),
    "chemistry":   (180, 105, 255),
    "biology":     (200, 120, 180),
    "mechanics":   (11, 158, 245),
}

COMPONENT_IMAGES = {
    "V":    "voltage_source.png",
    "R":    "resistor.png",
    "LED":  "led.png",
    "C":    "capacitor.png",
    "D":    "diode.png",
    "Q":    "transistor.png",
    "GND":  "ground.png",
    "GPIO": "gpio_block.png",
    "S":    "switch.png",
}

COMP_SIZE = 110           # rendered component size (px)
MARKER_STABLE_FRAMES = 6  # frames a marker must persist before switching
AUTOPLAY_INTERVAL = 2.2   # seconds per step in autoplay
RC_SLOWDOWN = 400.0       # real τ is ~1 ms; slow it 400× so humans can watch


# ═════════════════════════════ helpers ════════════════════════════
def get_component_type(comp_id: str) -> str:
    c = comp_id.upper()
    if c.startswith("LED"):
        return "LED"
    if c.startswith("GPIO"):
        return "GPIO"
    if c.startswith("GND"):
        return "GND"
    if c.startswith("RL") or c.startswith("R"):
        return "R"
    if c.startswith("S") and not c.startswith("SW"):
        return "S"
    return c[0]


def base_component(terminal: str) -> str:
    return terminal.split(".")[0]


def remove_background(img):
    """Convert light/checkerboard backgrounds to transparency."""
    if img is None:
        return None
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.shape[2] == 4:
        # trust existing alpha if it's meaningful
        if img[:, :, 3].min() < 250:
            return img
        img = img[:, :, :3]
    light = (img[:, :, 0] > 215) & (img[:, :, 1] > 200) & (img[:, :, 2] > 200)
    alpha = np.where(light, 0, 255).astype(np.uint8)
    b, g, r = cv2.split(img[:, :, :3])
    return cv2.merge([b, g, r, alpha])


def overlay_rgba(frame, img, cx, cy, scale=1.0):
    """Alpha-composite an RGBA sprite centred at (cx, cy)."""
    if img is None:
        return
    if scale != 1.0:
        img = cv2.resize(img, None, fx=scale, fy=scale,
                         interpolation=cv2.INTER_AREA)
    h, w = img.shape[:2]
    x1, y1 = cx - w // 2, cy - h // 2
    x2, y2 = x1 + w, y1 + h
    fx1, fy1 = max(x1, 0), max(y1, 0)
    fx2, fy2 = min(x2, frame.shape[1]), min(y2, frame.shape[0])
    if fx2 <= fx1 or fy2 <= fy1:
        return
    sx1, sy1 = fx1 - x1, fy1 - y1
    crop = img[sy1:sy1 + (fy2 - fy1), sx1:sx1 + (fx2 - fx1)]
    alpha = (crop[:, :, 3:4].astype(np.float32)) / 255.0
    roi = frame[fy1:fy2, fx1:fx2].astype(np.float32)
    frame[fy1:fy2, fx1:fx2] = (
        alpha * crop[:, :, :3].astype(np.float32) + (1 - alpha) * roi
    ).astype(np.uint8)


# ─────────────── vector fallback glyphs (no PNG needed) ───────────
def _glyph_canvas():
    return np.zeros((COMP_SIZE, COMP_SIZE, 4), np.uint8)


def draw_glyph(ctype: str):
    """Crisp vector component symbol on transparent canvas."""
    img = _glyph_canvas()
    c = COMP_SIZE // 2
    col = {"V": (11, 158, 245, 255), "GPIO": (237, 58, 124, 255),
           "LED": (80, 80, 250, 255), "C": (255, 212, 0, 255),
           "Q": (237, 58, 124, 255), "S": (129, 185, 16, 255),
           "GND": (200, 200, 200, 255)}.get(ctype, (255, 212, 0, 255))
    W = 5  # stroke

    if ctype == "R":
        pts = [(8, c)]
        xs = np.linspace(26, COMP_SIZE - 26, 7)
        for i, x in enumerate(xs):
            pts.append((int(x), c - 18 if i % 2 == 0 else c + 18))
        pts.append((COMP_SIZE - 8, c))
        cv2.polylines(img, [np.array(pts, np.int32)], False, col, W, cv2.LINE_AA)
    elif ctype == "V" or ctype == "GPIO":
        cv2.circle(img, (c, c), 34, col, W, cv2.LINE_AA)
        cv2.line(img, (c - 12, c), (c + 12, c), col, W, cv2.LINE_AA)
        cv2.line(img, (c, c - 12), (c, c + 12), col, W, cv2.LINE_AA)
        cv2.line(img, (8, c), (c - 34, c), col, W, cv2.LINE_AA)
        cv2.line(img, (c + 34, c), (COMP_SIZE - 8, c), col, W, cv2.LINE_AA)
        if ctype == "GPIO":
            cv2.putText(img, "GPIO", (c - 26, c + 45), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, col, 1, cv2.LINE_AA)
    elif ctype == "LED":
        p = np.array([(c - 16, c - 18), (c - 16, c + 18), (c + 14, c)], np.int32)
        cv2.polylines(img, [p], True, col, W - 1, cv2.LINE_AA)
        cv2.line(img, (c + 14, c - 18), (c + 14, c + 18), col, W - 1, cv2.LINE_AA)
        cv2.line(img, (8, c), (c - 16, c), col, W - 1, cv2.LINE_AA)
        cv2.line(img, (c + 14, c), (COMP_SIZE - 8, c), col, W - 1, cv2.LINE_AA)
        for dx in (0, 12):
            cv2.arrowedLine(img, (c + dx, c - 24), (c + dx + 12, c - 36),
                            col, 2, cv2.LINE_AA, tipLength=0.45)
    elif ctype == "C":
        cv2.line(img, (8, c), (c - 8, c), col, W, cv2.LINE_AA)
        cv2.line(img, (c + 8, c), (COMP_SIZE - 8, c), col, W, cv2.LINE_AA)
        cv2.line(img, (c - 8, c - 26), (c - 8, c + 26), col, W, cv2.LINE_AA)
        cv2.line(img, (c + 8, c - 26), (c + 8, c + 26), col, W, cv2.LINE_AA)
    elif ctype == "Q":
        cv2.circle(img, (c, c), 36, col, 3, cv2.LINE_AA)
        cv2.line(img, (c - 14, c - 22), (c - 14, c + 22), col, W, cv2.LINE_AA)
        cv2.line(img, (8, c), (c - 14, c), col, 3, cv2.LINE_AA)
        cv2.line(img, (c - 14, c - 10), (c + 20, c - 30), col, 3, cv2.LINE_AA)
        cv2.arrowedLine(img, (c - 14, c + 10), (c + 20, c + 30), col, 3,
                        cv2.LINE_AA, tipLength=0.3)
    elif ctype == "S":  # sensor / switch
        cv2.rectangle(img, (c - 30, c - 22), (c + 30, c + 22), col, 3, cv2.LINE_AA)
        cv2.circle(img, (c, c), 9, col, -1, cv2.LINE_AA)
        cv2.ellipse(img, (c, c), (18, 18), 0, -60, 60, col, 2, cv2.LINE_AA)
        cv2.ellipse(img, (c, c), (26, 26), 0, -50, 50, col, 2, cv2.LINE_AA)
    elif ctype == "GND":
        cv2.line(img, (c, 12), (c, c), col, W, cv2.LINE_AA)
        for i, w in enumerate((30, 20, 10)):
            cv2.line(img, (c - w, c + i * 12), (c + w, c + i * 12), col, W - 1, cv2.LINE_AA)
    else:
        cv2.circle(img, (c, c), 30, col, W, cv2.LINE_AA)
    return img


def load_component_image(comp_id: str):
    ctype = get_component_type(comp_id)
    fname = COMPONENT_IMAGES.get(ctype)
    if fname:
        p = ASSETS_DIR / fname
        if p.exists():
            img = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
            img = remove_background(img)
            if img is not None:
                return cv2.resize(img, (COMP_SIZE, COMP_SIZE),
                                  interpolation=cv2.INTER_AREA)
    return draw_glyph(ctype)


def fmt_r(ohms):
    return f"{ohms/1000:.1f} kOhm".replace(".0 ", " ") if ohms >= 1000 else f"{ohms:.0f} Ohm"


def fmt_i(amps):
    return f"{amps*1000:.2f} mA" if amps < 1 else f"{amps:.2f} A"


# ═══════════════════════════ layout engine ════════════════════════
class Layout:
    """
    Places components on a horizontal rail centred on screen and
    routes orthogonal wires between them. Parallel branches (RL, LED
    chains fed from a mid-node) drop to a second rail below.
    """

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.pos = {}          # comp -> (x, y) target
        self.smooth = {}       # comp -> (x, y) animated

    def compute(self, visible, connections):
        if not visible:
            self.pos = {}
            return
        n = len(visible)
        gap = min(190, (self.W - 320) // max(n - 1, 1)) if n > 1 else 0
        total = gap * (n - 1)
        x0 = (self.W - total) // 2
        y_main = int(self.H * 0.56)
        y_branch = y_main + 150

        # find parallel branch components (fed from a node that already
        # continues forward): heuristic — RL and anything after it that
        # returns to the source
        branch = set()
        for comp in visible:
            if comp.upper().startswith("RL") and comp.upper() != "RLED":
                branch.add(comp)

        rail = [c for c in visible if c not in branch]
        for i, compo in enumerate(rail):
            self.pos[compo] = (x0 + i * gap, y_main)
        for j, compo in enumerate(branch):
            # place under its feeding node (approx: under middle of rail)
            anchor = rail[min(len(rail) - 1, 2)]
            ax, _ = self.pos[anchor]
            self.pos[compo] = (ax + j * gap, y_branch)

    def update_smooth(self):
        for comp, (tx, ty) in self.pos.items():
            sx, sy = self.smooth.get(comp, (tx, ty + 40))
            self.smooth[comp] = (sx + (tx - sx) * 0.18, sy + (ty - sy) * 0.18)

    def get(self, comp):
        return tuple(map(int, self.smooth.get(comp, self.pos.get(comp, (0, 0)))))

    def wire_points(self, a, b):
        """Orthogonal route between two component edges."""
        ax, ay = self.get(a)
        bx, by = self.get(b)
        half = COMP_SIZE // 2 - 8
        if abs(ay - by) < 10:                     # same rail — straight
            if ax < bx:
                return [((ax + half, ay), (bx - half, by))]
            return [((ax - half, ay), (bx + half, by))]
        # different rails — L route
        mid_y = (ay + by) // 2
        return [((ax, ay + half if by > ay else ay - half), (ax, mid_y)),
                ((ax, mid_y), (bx, mid_y)),
                ((bx, mid_y), (bx, by - half if by > ay else by + half))]


# ═══════════════════════════ application ══════════════════════════
class CircuitVerseAR:
    def __init__(self, camera_index=0, window=(1280, 720)):
        self.W, self.H = window
        self.camera_index = camera_index

        self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_5X5_100)
        try:
            params = aruco.DetectorParameters()
            # more forgiving thresholds for typical webcams / screen-shown markers
            params.adaptiveThreshWinSizeMin = 3
            params.adaptiveThreshWinSizeMax = 45
            params.adaptiveThreshWinSizeStep = 6
            params.minMarkerPerimeterRate = 0.02   # detect smaller/farther markers
            params.maxMarkerPerimeterRate = 4.0
            params.polygonalApproxAccuracyRate = 0.05
            try:
                # subpixel corner refinement when available (sharper, steadier)
                params.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX
            except AttributeError:
                pass
            self.detector = aruco.ArucoDetector(self.aruco_dict, params)
        except AttributeError:                    # OpenCV < 4.7 fallback
            self.detector = None

        self.reset_experiment_state()
        self.marker_candidate = None
        self.marker_votes = 0
        self.current_marker = None
        self.autoplay = False
        self.last_autoplay = 0.0
        self.flow = effects.CurrentFlow()
        self.ambient = effects.Ambient(n=64)
        self.layout = Layout(self.W, self.H)
        self.t_start = time.time()
        self.toast = None                          # (text, expiry)

        # experiment menu (primary UI; markers still work as fallback)
        self.menu = ExperimentMenu(EXPERIMENT_CATALOG)
        self.menu.on_pick = self.select_experiment

    # ─────────────────────────── state ────────────────────────────
    def reset_experiment_state(self):
        self.circuit = None
        self.steps = []
        self.raw = {}
        self.exp_name = ""
        self.domain = "electronics"
        self.scene = None
        self.current_step = -1
        self.visible = []
        self.images = {}
        self.connections = []
        self.explain_msg = None                    # (text, shown_at)
        self.solution = None
        self.rc_t0 = None

    def select_experiment(self, marker_id):
        """Menu pick — load an experiment exactly as a marker would, but
        pin it so a stray marker in view doesn't override the choice."""
        self.load_marker(marker_id)
        self.current_marker = marker_id
        self.marker_candidate = None
        self.marker_votes = 0

    def load_marker(self, marker_id):
        fname = EXPERIMENT_FILES.get(marker_id)
        if not fname:
            self.toast = (f"Marker {marker_id}: no experiment mapped", time.time() + 3)
            return
        path = EXPERIMENTS_DIR / fname
        if not path.exists():
            self.toast = (f"Missing file: {fname}", time.time() + 3)
            return
        try:
            circuit, steps, raw = load_experiment(path)
        except (json.JSONDecodeError, KeyError) as e:
            self.toast = (f"Bad JSON in {fname}: {e}", time.time() + 4)
            return
        self.reset_experiment_state()
        self.circuit, self.steps, self.raw = circuit, steps, raw
        self.exp_name = raw.get("name", fname)
        self.domain = raw.get("domain", "electronics")
        self.scene = create_scene(raw, self.W, self.H)
        self.current_marker = marker_id
        self.toast = (f"Experiment loaded — press N to begin", time.time() + 3.5)

    # ────────────────────── step state machine ────────────────────
    def apply_steps(self, upto):
        """Rebuild visible/connections deterministically from steps[0..upto]."""
        self.visible, self.connections = [], []
        self.explain_msg, self.rc_t0 = None, None

        # domain scenes: drive the Scene object instead of the circuit builder
        if self.scene is not None:
            self.scene.reset()
            for i in range(upto + 1):
                step = self.steps[i]
                st = step.get("type")
                if st == "show_component":
                    self.scene.show(step["target"])
                elif st == "animate":
                    self.scene.animate(step["target"])
                elif st == "explain" and i == upto:
                    self.explain_msg = (step.get("text", ""), time.time())
            return

        for i in range(upto + 1):
            step = self.steps[i]
            st = step.get("type")
            if st == "show_component":
                comp = step["target"]
                if comp not in self.visible:
                    self.visible.append(comp)
                    if comp not in self.images:
                        self.images[comp] = load_component_image(comp)
            elif st == "connect":
                a, b = base_component(step["from"]), base_component(step["to"])
                if (a, b) not in self.connections and (b, a) not in self.connections:
                    self.connections.append((a, b))
            elif st == "explain" and i == upto:
                self.explain_msg = (step.get("text", ""), time.time())

        # start RC clock the moment the RC loop closes
        if self.circuit and self.circuit.ctype == "rc" and self._loop_closed():
            self.rc_t0 = time.time()

        self.layout.compute(self.visible, self.connections)
        self.solution = solve(self.circuit) if self._loop_closed() else None

    def _loop_closed(self):
        """Heuristic: circuit is 'live' once every visible component is wired."""
        if not self.connections or not self.circuit:
            return False
        wired = {c for pair in self.connections for c in pair}
        core = [v for v in self.visible if not v.upper().startswith("GND")]
        return len(core) >= 2 and all(c in wired for c in core)

    def next_step(self):
        if self.steps and self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.apply_steps(self.current_step)

    def back_step(self):
        if self.current_step >= 0:
            self.current_step -= 1
            if self.current_step >= 0:
                self.apply_steps(self.current_step)
            else:
                self._clear_build()

    def _clear_build(self):
        self.visible, self.connections = [], []
        self.explain_msg, self.solution, self.rc_t0 = None, None, None

    # ═════════════════════════ rendering ══════════════════════════
    def _domain_tint(self):
        return {"chemistry": (255, 150, 210),
                "biology":   (200, 160, 255),
                "physics":   (255, 190, 120),
                "circuits":  (150, 255, 180),
                "mechanics": (120, 200, 255),
                "electronics": (255, 200, 120)}.get(self.domain, (255, 200, 120))

    def render(self, frame, corners_list, ids):
        t = time.time() - self.t_start
        effects.vignette(frame, 0.34)
        self.ambient.draw(frame, tint=self._domain_tint())
        effects.scanline(frame, t)

        # marker lock rings
        if ids is not None:
            for c, mid in zip(corners_list, ids.flatten()):
                effects.marker_lock(frame, c, str(mid))

        # ── domain scenes render their own content area ──
        if self.scene is not None:
            self.scene.render(frame)
            self._draw_topbar(frame)
            self._draw_step_panel(frame)
            if self.explain_msg:
                self._draw_explain(frame)
            self._draw_toast(frame)
            self._draw_controls(frame)
            effects.bloom(frame, strength=0.16)
            effects.corner_flourish(frame, t)
            return frame

        self.layout.update_smooth()

        # ── wires + current flow ──
        i_now = self.solution["current"] if self.solution else 0.0
        # RC transient: I(t) = (V/R)·e^(−t/τ) — particles slow as cap charges
        if (self.rc_t0 and self.solution and self.solution.get("rc")
                and self.solution["rc"]["tau"] > 0):
            rc = self.solution["rc"]
            t_sim = (time.time() - self.rc_t0) / RC_SLOWDOWN
            i_now = (rc["v_final"] / rc["R"]) * math.exp(-t_sim / rc["tau"])
        self._i_display = i_now
        active = i_now > 1e-6
        wire_segments = []
        for a, b in self.connections:
            if a in self.visible and b in self.visible:
                for p1, p2 in self.layout.wire_points(a, b):
                    effects.glow_wire(frame, p1, p2, GREEN, active)
                    wire_segments.append((p1, p2))
        if active:
            self.flow.draw(frame, wire_segments, i_now)

        # ── components ──
        for comp in self.visible:
            x, y = self.layout.get(comp)
            if self.solution and comp in self.solution["led_status"]:
                effects.led_glow(frame, x, y, self.solution["led_status"][comp])
            overlay_rgba(frame, self.images.get(comp), x, y)

            # name label
            tw, _ = text_size(comp, 0.5, 1, hud.FONT_S)
            text(frame, comp, x - tw // 2, y + COMP_SIZE // 2 + 20,
                 0.5, TEXT, 1, hud.FONT_S)

            # live value tag — staggered so adjacent tags never collide
            if self.solution:
                tag = self._value_for(comp)
                if tag:
                    idx = self.visible.index(comp)
                    stagger = -36 if idx % 2 else 0
                    value_tag(frame, x - COMP_SIZE // 2,
                              y - COMP_SIZE // 2 - 30 + stagger, comp, tag,
                              self._tag_color(comp))

        # ── HUD layers ──
        self._draw_topbar(frame)
        self._draw_step_panel(frame)
        if self.solution:
            self._draw_solution_panel(frame)
        if self.rc_t0 and self.solution and self.solution.get("rc"):
            rc = self.solution["rc"]
            rc_graph(frame, self.W - 330, self.H - 235, 310, 190,
                     rc["tau"], rc["v_final"],
                     (time.time() - self.rc_t0) / RC_SLOWDOWN)
        if self.explain_msg:
            self._draw_explain(frame)
        self._draw_toast(frame)
        self._draw_controls(frame)
        effects.bloom(frame, strength=0.16)
        effects.corner_flourish(frame, time.time() - self.t_start)
        return frame

    # ───────────────────────── HUD widgets ─────────────────────────
    def _value_for(self, comp):
        s = self.solution
        parts = []
        if comp in s["voltage_drops"]:
            parts.append(f"{s['voltage_drops'][comp]:.2f} V")
        if comp in s["currents"]:
            parts.append(fmt_i(s["currents"][comp]))
        r = self.circuit.resistor(comp) if self.circuit else None
        if r:
            parts.insert(0, fmt_r(r.resistance))
        if comp == self.circuit.source.name:
            parts = [f"{self.circuit.source.voltage:.1f} V", fmt_i(s["current"])]
        return " · ".join(parts) if parts else None

    def _tag_color(self, comp):
        if self.solution and self.solution["led_status"].get(comp, "") == "OVERCURRENT":
            return RED
        return ACCENT

    def _draw_topbar(self, frame):
        glass_panel(frame, 16, 14, self.W - 32, 62, radius=16)
        # logo
        text(frame, "CIRCUIT", 36, 52, 0.85, TEXT, 2)
        w1, _ = text_size("CIRCUIT", 0.85, 2)
        text(frame, "VERSE", 36 + w1, 52, 0.85, ACCENT, 2)
        w2, _ = text_size("VERSE", 0.85, 2)
        chip(frame, "v2.0 AR LAB", 52 + w1 + w2, 30, PURPLE)

        if self.exp_name:
            title = self.exp_name if len(self.exp_name) < 46 else self.exp_name[:43] + "..."
            tw, _ = text_size(title, 0.55, 1, hud.FONT_S)
            text(frame, title, self.W - tw - 190, 40, 0.55, TEXT, 1, hud.FONT_S)
            done = self.current_step + 1
            progress_bar(frame, self.W - tw - 190, 52, tw, done, len(self.steps))
            chip(frame, f"MARKER {self.current_marker}", self.W - 150, 30, GREEN)
        else:
            s = "SCANNING FOR MARKER"
            pulse = 0.5 + 0.5 * math.sin(time.time() * 3)
            col = tuple(int(m + (a - m) * pulse) for m, a in zip(MUTED, ACCENT))
            tw, _ = text_size(s, 0.5, 1, hud.FONT_S)
            text(frame, s, self.W - tw - 60, 46, 0.5, col, 1, hud.FONT_S)

    def _draw_step_panel(self, frame):
        if not self.steps:
            return
        if self.current_step < 0:
            msg, col = "Press  N  to start the experiment", ACCENT
        else:
            step = self.steps[self.current_step]
            msg = step.get("text", "")
            col = {"show_component": ACCENT, "connect": GREEN,
                   "explain": PURPLE}.get(step.get("type"), TEXT)
        pw = min(760, self.W - 380)
        lines = hud.wrap_px(msg, pw - 40, scale=0.52)
        ph = 46 + 26 * len(lines)
        glass_panel(frame, 16, self.H - ph - 16, pw, ph, radius=16, border=col)
        step_no = f"STEP {self.current_step + 1}/{len(self.steps)}" \
            if self.current_step >= 0 else "READY"
        chip(frame, step_no, 32, self.H - ph - 2, col)
        for i, line in enumerate(lines):
            text(frame, line, 32, self.H - ph + 40 + i * 26, 0.52, TEXT, 1, hud.FONT_S)

    def _draw_solution_panel(self, frame):
        s = self.solution
        rows = [("SUPPLY", f"{s['supply_voltage']:.1f} V", AMBER)]
        if s["total_resistance"] > 0:
            rows.append(("TOTAL R", fmt_r(s["total_resistance"]), ACCENT))
        i_show = getattr(self, "_i_display", s["current"])
        rows.append(("CURRENT", fmt_i(i_show), GREEN))
        for led, st in s["led_status"].items():
            rows.append((led, st, RED if "OVER" in st else
                        (GREEN if st == "ON" else MUTED)))
        if s.get("rc"):
            rows.append(("TAU (τ)", f"{s['rc']['tau']*1000:.1f} ms", PURPLE))
        if s.get("sensor"):
            sen = s["sensor"]
            rows.append(("SENSOR", f"{sen['value']:.0f}% / thr {sen['threshold']:.0f}%",
                         GREEN if sen["active"] else MUTED))

        ph = 58 + 30 * len(rows)
        x0, y0 = self.W - 264, 92
        glass_panel(frame, x0, y0, 248, ph, radius=16, border=ACCENT)
        text(frame, "LIVE SIMULATION", x0 + 16, y0 + 28, 0.5, ACCENT, 1, hud.FONT_S)
        cv2.line(frame, (x0 + 16, y0 + 38), (x0 + 232, y0 + 38), (70, 60, 45), 1)
        for i, (k, v, col) in enumerate(rows):
            yy = y0 + 64 + i * 30
            text(frame, k, x0 + 16, yy, 0.44, MUTED, 1, hud.FONT_S)
            vw, _ = text_size(v, 0.48, 1, hud.FONT_S)
            text(frame, v, x0 + 232 - vw, yy, 0.48, col, 1, hud.FONT_S)

    def _draw_explain(self, frame):
        msg, shown = self.explain_msg
        if time.time() - shown > 8:
            return
        pw = 520
        lines = hud.wrap_px(msg, pw - 44, scale=0.52)
        ph = 56 + 26 * len(lines)
        x0 = (self.W - pw) // 2
        y0 = 96
        glass_panel(frame, x0, y0, pw, ph, radius=18,
                    border=PURPLE, tint_strength=0.62)
        chip(frame, "CONCEPT", x0 + 16, y0 - 12, PURPLE)
        for i, line in enumerate(lines):
            text(frame, line, x0 + 22, y0 + 42 + i * 26, 0.52, TEXT, 1, hud.FONT_S)

    def _draw_toast(self, frame):
        if not self.toast:
            return
        msg, expiry = self.toast
        if time.time() > expiry:
            self.toast = None
            return
        tw, _ = text_size(msg, 0.5, 1, hud.FONT_S)
        x0 = (self.W - tw - 40) // 2
        glass_panel(frame, x0, self.H - 120, tw + 40, 40,
                    radius=20, border=AMBER)
        text(frame, msg, x0 + 20, self.H - 94, 0.5, AMBER, 1, hud.FONT_S)

    def _draw_controls(self, frame):
        s = "M menu   N next   B back   R reset   SPACE auto   Q quit"
        if self.autoplay:
            s = "AUTOPLAY ON   ·   " + s
        tw, _ = text_size(s, 0.42, 1, hud.FONT_S)
        text(frame, s, self.W - tw - 24, self.H - 18, 0.42,
             GREEN if self.autoplay else MUTED, 1, hud.FONT_S)

    # ═══════════════════════════ main loop ════════════════════════
    def _on_mouse(self, event, x, y, flags, param):
        """Map window pixel coords to render-space before the menu sees them.
        In a normal window coords map 1:1. In fullscreen the image is scaled
        and letterboxed, so we account for both scale and centering offset."""
        if getattr(self, "fullscreen", False):
            try:
                import cv2 as _cv2
                _, _, ww, wh = _cv2.getWindowImageRect(self._win_name)
                if ww > 0 and wh > 0:
                    scale = min(ww / self.W, wh / self.H)
                    if scale > 0:
                        off_x = (ww - self.W * scale) / 2
                        off_y = (wh - self.H * scale) / 2
                        x = int((x - off_x) / scale)
                        y = int((y - off_y) / scale)
            except Exception:
                pass
        self.menu.handle_mouse(event, x, y, flags, param)

    def _mirror_corners(self, corners):
        """Flip detected marker corner x-coords to match the mirrored frame."""
        if not corners:
            return corners
        out = []
        for c in corners:
            c = c.copy()
            c[:, :, 0] = self.W - 1 - c[:, :, 0]
            out.append(c)
        return out

    def detect(self, gray):
        if self.detector:
            corners, ids, _ = self.detector.detectMarkers(gray)
        else:
            corners, ids, _ = aruco.detectMarkers(gray, self.aruco_dict)
        return corners, ids

    def handle_marker(self, ids):
        if ids is None:
            self.marker_votes = max(0, self.marker_votes - 1)
            return
        mid = int(ids.flatten()[0])
        if mid == self.current_marker:
            return
        if mid == self.marker_candidate:
            self.marker_votes += 1
            if self.marker_votes >= MARKER_STABLE_FRAMES:
                self.load_marker(mid)
                self.marker_votes = 0
        else:
            self.marker_candidate, self.marker_votes = mid, 1

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            print("\n[CircuitVerse] Could not open camera index "
                  f"{self.camera_index}.")
            print("  - Make sure a webcam is connected and not used by another app.")
            print("  - Try a different index: CircuitVerseAR(camera_index=1).run()\n")
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.H)

        win = "CircuitVerse v2.0 - AR Lab"
        self._win_name = win
        cv2.namedWindow(win, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win, self.W, self.H)
        cv2.setMouseCallback(win, self._on_mouse)
        # start windowed (coords map 1:1 so the menu is reliably clickable);
        # press F to go fullscreen
        self.fullscreen = False
        print(__doc__)

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Camera read failed."); break
            frame = cv2.resize(frame, (self.W, self.H))

            # IMPORTANT: detect on the UN-mirrored frame. ArUco markers are
            # asymmetric, so a mirrored image never matches the dictionary.
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners, ids = self.detect(gray)

            # now mirror the frame for a natural selfie view, and mirror the
            # detected corner x-coords to match the flipped image
            frame = cv2.flip(frame, 1)
            corners = self._mirror_corners(corners)

            # markers act only as a fallback; ignore them while menu is open
            if not self.menu.expanded:
                self.handle_marker(ids)

            frame = self.render(frame, corners, ids)
            self.menu.draw(frame)
            cv2.imshow(win, frame)

            if self.autoplay and self.steps and \
               time.time() - self.last_autoplay > AUTOPLAY_INTERVAL:
                self.last_autoplay = time.time()
                if self.current_step < len(self.steps) - 1:
                    self.next_step()
                else:
                    self.autoplay = False

            key = cv2.waitKey(1) & 0xFF
            if key == 255:
                continue
            # menu gets first crack at the key; if consumed, skip app controls
            if self.menu.handle_key(key):
                continue
            if key == ord("n"):
                self.next_step()
            elif key == ord("b"):
                self.back_step()
            elif key == ord("r"):
                self.current_step = -1
                self._clear_build()
                if self.scene:
                    self.scene.reset()
            elif key == ord(" "):
                self.autoplay = not self.autoplay
                self.last_autoplay = 0
            elif key == ord("f"):
                self.fullscreen = not self.fullscreen
                cv2.setWindowProperty(
                    win, cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_FULLSCREEN if self.fullscreen else cv2.WINDOW_NORMAL)
            elif key == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    CircuitVerseAR().run()
