# circuit_engine/loader.py
"""Universal experiment loader for CircuitVerse v2."""

import json
from pathlib import Path
from typing import Union, Tuple, List

from .components import VoltageSource, Resistor, Led, Capacitor, Transistor, Sensor
from .circuit import Circuit


def load_experiment(path: Union[str, Path]) -> Tuple[Circuit, List[dict], dict]:
    """
    Load any experiment JSON.
    Returns (Circuit, steps, raw_data).
    Future domains (chemistry/biology/mechanics) hook in via data["domain"].
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    src = data["source"]
    source = VoltageSource(name=src["name"], voltage=float(src["voltage"]))

    resistors = [
        Resistor(name=r["name"], resistance=float(r["resistance"]))
        for r in data.get("resistors", [])
    ]
    leds = [
        Led(
            name=l["name"],
            forward_voltage=float(l["forward_voltage"]),
            max_current=float(l["max_current"]),
        )
        for l in data.get("leds", [])
    ]
    capacitors = [
        Capacitor(name=c["name"], capacitance=float(c["capacitance"]))
        for c in data.get("capacitors", [])
    ]

    transistor = None
    if "transistor" in data:
        t = data["transistor"]
        transistor = Transistor(name=t["name"], type=t.get("type", "NPN"))

    sensor = None
    if "sensor" in data:
        s = data["sensor"]
        sensor = Sensor(
            name=s["name"],
            kind=s.get("kind", "generic"),
            unit=s.get("unit", "percentage"),
            min_value=float(s.get("min_value", 0)),
            max_value=float(s.get("max_value", 100)),
            threshold=float(s.get("threshold", 50)),
        )

    circuit = Circuit(
        source=source,
        ctype=data.get("type", "series"),
        name=data.get("name", path.stem),
        resistors=resistors,
        leds=leds,
        capacitors=capacitors,
        transistor=transistor,
        sensor=sensor,
    )
    return circuit, data.get("steps", []), data


# Backward-compatible v1 API
def load_series_circuit_from_json(path):
    circuit, steps, _ = load_experiment(path)
    return circuit, steps
