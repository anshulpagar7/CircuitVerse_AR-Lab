# circuit_engine/components.py
"""Component models for CircuitVerse v2 — all experiment domains."""

from dataclasses import dataclass


@dataclass
class VoltageSource:
    """DC voltage source (battery, power supply, or GPIO pin)."""
    name: str
    voltage: float  # Volts


@dataclass
class Resistor:
    """Ideal resistor."""
    name: str
    resistance: float  # Ohms


@dataclass
class Led:
    """LED with forward voltage drop and max safe current."""
    name: str
    forward_voltage: float  # Volts
    max_current: float      # Amps


@dataclass
class Capacitor:
    """Ideal capacitor for RC transient experiments."""
    name: str
    capacitance: float  # Farads


@dataclass
class Transistor:
    """BJT switch model (NPN/PNP)."""
    name: str
    type: str = "NPN"
    vbe_on: float = 0.7    # base-emitter turn-on voltage
    vce_sat: float = 0.2   # collector-emitter saturation voltage
    beta: float = 100.0    # current gain


@dataclass
class Sensor:
    """Generic threshold sensor (IR / gas / LDR ...)."""
    name: str
    kind: str = "generic"
    unit: str = "percentage"
    min_value: float = 0.0
    max_value: float = 100.0
    threshold: float = 50.0
