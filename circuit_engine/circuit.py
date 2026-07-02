# circuit_engine/circuit.py
"""Circuit container for CircuitVerse v2."""

from dataclasses import dataclass, field
from typing import List, Optional
from .components import VoltageSource, Resistor, Led, Capacitor, Transistor, Sensor


@dataclass
class Circuit:
    """
    Universal circuit container.
    `ctype` mirrors the experiment JSON "type" field:
      series | parallel | rc | digital | transistor_switch | sensor_threshold
    """
    source: VoltageSource
    ctype: str = "series"
    name: str = ""
    resistors: List[Resistor] = field(default_factory=list)
    leds: List[Led] = field(default_factory=list)
    capacitors: List[Capacitor] = field(default_factory=list)
    transistor: Optional[Transistor] = None
    sensor: Optional[Sensor] = None

    def total_series_resistance(self) -> float:
        return sum(r.resistance for r in self.resistors)

    def resistor(self, name: str) -> Optional[Resistor]:
        for r in self.resistors:
            if r.name == name:
                return r
        return None


# Backward-compatible alias (v1 code imported SeriesCircuit)
SeriesCircuit = Circuit
