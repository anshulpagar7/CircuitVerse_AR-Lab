# CircuitVerse v2 — AR Multi-Domain Science Laboratory

An Augmented Reality science lab that turns any webcam into an interactive,
physics-accurate learning platform spanning **Physics, Chemistry, Biology, and Circuits**.
Browse experiments from a cinematic glass menu, or show a printed ArUco marker.

![version](https://img.shields.io/badge/version-2.0-00d4ff) ![python](https://img.shields.io/badge/python-3.9%E2%80%933.12-blue) ![experiments](https://img.shields.io/badge/experiments-21-7c3aed) ![domains](https://img.shields.io/badge/subjects-4-f59e0b)

## Two ways in

1. **Menu (primary)** — click `☰ MENU` or press `M`, pick a subject, pick an
   experiment. Full mouse + keyboard (arrows, Enter, number keys).
2. **ArUco markers (fallback)** — show marker 0–20 to the camera; it loads
   automatically. Print `markers/CircuitVerse_Markers.pdf` at 100% scale.

Both paths run the same engine, fullscreen, with the camera mirrored.

## 21 experiments, all live vector simulations

### ⚡ Physics (9)
| # | Experiment | What you see |
|---|---|---|
| 0 | Simple Harmonic Motion | Mass-spring + live oscilloscope sine trace |
| 1 | Resonance | Frequency sweep, resonance peak curve |
| 2 | Young's Double-Slit | Circular wavefronts + interference fringes |
| 3 | Converging Lens | Three-ray diagram, live image formation |
| 4 | Refraction & TIR | Snell's law bending, total internal reflection |
| 5 | DC Motor | Field, current loop, F = BIL torque, rotation |
| 6 | EM Induction | Magnet through coil, galvanometer needle, Faraday EMF |
| 7 | Photoelectric Effect | Photons ejecting electrons, threshold frequency |
| 8 | Bohr Model | Electron orbits, energy-level jumps, photon emission |

### 🧪 Chemistry (4)
Acid-Base Titration (live pH curve) · Electrolysis (2:1 H₂:O₂ bubbles) ·
Flame Test (characteristic ion colours) · Reaction Rate (collision theory + heat)

### 🔬 Biology (4)
Animal Cell Anatomy · DNA Replication · Neuron Action Potential (live membrane trace) ·
Photosynthesis (chloroplast, light → glucose + O₂)

### ⚡ Circuits (4) — real instruments, animated meters
| # | Experiment | Instruments |
|---|---|---|
| 17 | Ohm's Law | Ammeter (series) + Voltmeter (parallel) on a live loop |
| 18 | Series — Voltage Division | Ammeter + movable voltmeter, per-resistor drops |
| 19 | Parallel — Current Division | Total + per-branch ammeters, current splits |
| 20 | Wheatstone Bridge | Galvanometer null detection for an unknown Rx |

Each circuit is drawn as animated vector art with analog dial meters whose
needles swing to the live reading, glowing wires, and current-flow particles.
Physics is computed by `circuit_engine.solver`.

## What makes it special

- **Real physics, computed live.** SHM integrates the equation of motion; the lens solves 1/f = 1/v + 1/u each frame; refraction applies Snell's law with a real critical angle; the photoelectric verdict uses KE = hf − φ.
- **Cinematic "maximum-wow" visuals** — gradient frosted glass, neon double borders, outer-glow bloom on every bright element, drifting ambient motes tinted per subject, animated HUD corner brackets, and a vignette for depth.
- **Fullscreen + mirrored camera** — launches fullscreen (toggle with `F`); the feed is mirrored so it reads naturally.
- **No boring asset PNGs** — every experiment is drawn as crisp animated vector art, the same technique across all three subjects.

## Quick start

```bash
pip install -r requirements.txt
python python_app/ar_main.py
```

## Controls

| Key / Action | Effect |
|---|---|
| `M` or ☰ | open / close experiment menu |
| mouse / ↑↓ + Enter / `1`–`9` | navigate menu |
| `N` / `B` | next / previous step |
| `SPACE` | autoplay · `R` reset · `F` fullscreen · `Q` quit |

## Project structure

```
CircuitVerse/
├── python_app/
│   ├── ar_main.py      # engine, state machine, app loop, fullscreen, catalog
│   ├── menu.py         # cinematic glass experiment menu
│   ├── hud.py          # glassmorphism + gradient + glow rendering
│   └── effects.py      # particles, bloom, ambient motes, vignette, lock rings
├── domains/
│   ├── physics.py      # 9 physics scenes (waves, optics, EM, modern)
│   ├── chemistry.py    # titration, electrolysis, flame test, reaction rate
│   ├── biology.py      # cell, DNA, neuron, photosynthesis
│   └── mechanics.py    # pendulum, projectile (legacy, still available)
├── circuit_engine/     # electronics solver (kept for future circuit experiments)
├── experiments/        # 17 experiment JSONs
├── markers/            # printable ArUco markers 0–16 + combined PDF sheet
└── requirements.txt
```

## Adding an experiment

1. Add a `Scene` subclass in the relevant `domains/*.py`.
2. Register its `type` in `domains/__init__.py`.
3. Drop a JSON in `experiments/` and add it to `EXPERIMENT_CATALOG` (and `EXPERIMENT_FILES` for a marker).

The menu, HUD, fullscreen, and step machine pick it up automatically.

## Author

**Anshul Pagar** · B.Tech CSE · SRM Institute of Science and Technology
