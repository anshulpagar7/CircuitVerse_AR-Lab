# domains/__init__.py
"""
CircuitVerse v2 — multi-domain scene router.

Every non-electronics experiment JSON declares:  "domain": "chemistry" | "biology" | "mechanics"
A Scene owns the content area (objects, animations, simulations, graphs);
the shared HUD chrome (top bar, step panel, toasts) stays in ar_main.
"""


class Scene:
    """Base scene — step-driven object visibility + animation flags."""

    ACCENT_KEY = "accent"

    def __init__(self, raw: dict, W: int, H: int):
        self.raw = raw
        self.W, self.H = W, H
        self.sim = raw.get("simulation", {})
        self.visible = []       # shown object names, in order
        self.animations = set() # active animation target names
        self.t0 = None          # set when first animation starts

    # ── step machine (called by ar_main.apply_steps) ──
    def reset(self):
        self.visible, self.animations, self.t0 = [], set(), None

    def show(self, target: str):
        if target not in self.visible:
            self.visible.append(target)

    def animate(self, target: str):
        import time
        self.animations.add(target)
        if self.t0 is None:
            self.t0 = time.time()

    def elapsed(self):
        import time
        return 0.0 if self.t0 is None else time.time() - self.t0

    def render(self, frame):
        raise NotImplementedError


def create_scene(raw: dict, W: int, H: int):
    domain = raw.get("domain", "electronics")
    if domain == "electronics":
        return None
    if domain == "chemistry":
        from .chemistry import TitrationScene, ElectrolysisScene
        return {"titration": TitrationScene,
                "electrolysis": ElectrolysisScene}[raw["type"]](raw, W, H)
    if domain == "biology":
        from .biology import CellScene, DNAScene
        return {"cell_anatomy": CellScene,
                "dna_replication": DNAScene}[raw["type"]](raw, W, H)
    if domain == "mechanics":
        from .mechanics import PendulumScene, ProjectileScene
        return {"pendulum": PendulumScene,
                "projectile": ProjectileScene}[raw["type"]](raw, W, H)
    return None
