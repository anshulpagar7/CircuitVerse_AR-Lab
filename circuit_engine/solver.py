# circuit_engine/solver.py
"""
Universal solver for CircuitVerse v2.

Dispatches on circuit.ctype and returns a unified result dict consumed
by the AR HUD:

{
  "topology":       str,
  "supply_voltage": float,
  "current":        float (main loop current, A),
  "total_resistance": float,
  "voltage_drops":  {comp_name: volts},
  "currents":       {comp_name: amps},     # per-branch where relevant
  "led_status":     {led_name: "ON"|"OFF"|"OVERCURRENT"},
  "rc":             {"tau": s, "v_final": V}  (rc circuits only)
  "notes":          [str, ...]              # human-readable insights
}
"""

import math
from typing import Dict, Any
from .circuit import Circuit


def _base_result(circuit: Circuit) -> Dict[str, Any]:
    return {
        "topology": circuit.ctype,
        "supply_voltage": circuit.source.voltage,
        "current": 0.0,
        "total_resistance": 0.0,
        "voltage_drops": {},
        "currents": {},
        "led_status": {},
        "rc": None,
        "notes": [],
    }


# ---------------------------------------------------------------- series
def _solve_series(circuit: Circuit) -> Dict[str, Any]:
    res = _base_result(circuit)
    V = circuit.source.voltage
    led_drop = sum(l.forward_voltage for l in circuit.leds)
    R = circuit.total_series_resistance()
    res["total_resistance"] = R

    if led_drop >= V or R <= 0:
        for led in circuit.leds:
            res["led_status"][led.name] = "OFF"
        res["notes"].append("Insufficient voltage — no current flows.")
        return res

    I = (V - led_drop) / R
    res["current"] = I
    for r in circuit.resistors:
        res["voltage_drops"][r.name] = I * r.resistance
        res["currents"][r.name] = I
    for led in circuit.leds:
        res["voltage_drops"][led.name] = led.forward_voltage
        res["currents"][led.name] = I
        res["led_status"][led.name] = "ON" if I <= led.max_current else "OVERCURRENT"

    res["notes"].append(f"Ohm's law: I = V/R = {I*1000:.2f} mA")
    return res


# ------------------------------------------------------------- parallel
def _solve_divider_with_load(circuit: Circuit) -> Dict[str, Any]:
    """
    Voltage divider R1–R2 with load RL parallel to R2.
    Falls back to series solving if the R1/R2/RL pattern isn't found.
    """
    res = _base_result(circuit)
    r1 = circuit.resistor("R1")
    r2 = circuit.resistor("R2")
    rl = circuit.resistor("RL")
    V = circuit.source.voltage

    if not (r1 and r2):
        return _solve_series(circuit)

    if rl:
        r2_eff = (r2.resistance * rl.resistance) / (r2.resistance + rl.resistance)
    else:
        r2_eff = r2.resistance

    total = r1.resistance + r2_eff
    I_total = V / total
    v_out = I_total * r2_eff

    res["total_resistance"] = total
    res["current"] = I_total
    res["voltage_drops"][r1.name] = I_total * r1.resistance
    res["voltage_drops"][r2.name] = v_out
    res["currents"][r1.name] = I_total
    res["currents"][r2.name] = v_out / r2.resistance
    if rl:
        res["voltage_drops"][rl.name] = v_out
        res["currents"][rl.name] = v_out / rl.resistance
        unloaded = V * r2.resistance / (r1.resistance + r2.resistance)
        res["notes"].append(
            f"Vout loaded {v_out:.2f} V vs unloaded {unloaded:.2f} V — load pulls it down."
        )
    return res


# ------------------------------------------------------------------- rc
def _solve_rc(circuit: Circuit) -> Dict[str, Any]:
    res = _solve_series(circuit)  # DC steady state through resistor chain
    if circuit.capacitors:
        C = circuit.capacitors[0].capacitance
        R = circuit.total_series_resistance()
        tau = R * C
        res["rc"] = {
            "tau": tau,
            "v_final": circuit.source.voltage - sum(l.forward_voltage for l in circuit.leds),
            "R": R,
            "C": C,
        }
        res["notes"].append(f"τ = R×C = {tau*1000:.2f} ms — 99% charged at 5τ.")
        # At steady state the cap blocks DC: loop current -> 0
        res["current"] = 0.0
        res["notes"].append("Steady state: capacitor fully charged, I → 0.")
    return res


def rc_voltage_at(t: float, tau: float, v_final: float, charging: bool = True) -> float:
    """Vc(t) for charging or discharging — used by the AR live graph."""
    if tau <= 0:
        return v_final if charging else 0.0
    if charging:
        return v_final * (1.0 - math.exp(-t / tau))
    return v_final * math.exp(-t / tau)


# ------------------------------------------------------- transistor switch
def _solve_transistor_switch(circuit: Circuit) -> Dict[str, Any]:
    res = _base_result(circuit)
    q = circuit.transistor
    V = circuit.source.voltage
    r_base = circuit.resistor("R_base")
    r_led = circuit.resistor("R_led")
    led = circuit.leds[0] if circuit.leds else None

    if not (q and r_base and r_led and led):
        return _solve_series(circuit)

    # Base drive
    I_b = max((V - q.vbe_on) / r_base.resistance, 0.0)
    # Collector loop if saturated
    I_c_sat = (V - led.forward_voltage - q.vce_sat) / r_led.resistance
    saturated = q.beta * I_b >= I_c_sat > 0

    res["currents"]["Q1.base"] = I_b
    if saturated:
        res["current"] = I_c_sat
        res["currents"][led.name] = I_c_sat
        res["voltage_drops"][r_led.name] = I_c_sat * r_led.resistance
        res["voltage_drops"][led.name] = led.forward_voltage
        res["led_status"][led.name] = "ON" if I_c_sat <= led.max_current else "OVERCURRENT"
        res["notes"].append(
            f"Q1 SATURATED: Ib={I_b*1000:.2f} mA drives Ic={I_c_sat*1000:.1f} mA."
        )
    else:
        res["led_status"][led.name] = "OFF"
        res["notes"].append("Base drive too low — Q1 is OFF, LED is OFF.")
    return res


# ------------------------------------------------------- sensor threshold
def _solve_sensor_threshold(circuit: Circuit, sensor_value: float = None) -> Dict[str, Any]:
    res = _base_result(circuit)
    s = circuit.sensor
    if not s:
        return _solve_series(circuit)
    value = s.threshold + 10 if sensor_value is None else sensor_value
    active = value >= s.threshold
    for led in circuit.leds:
        res["led_status"][led.name] = "ON" if active else "OFF"
    res["notes"].append(
        f"Sensor {value:.0f}{'%' if s.unit=='percentage' else s.unit} "
        f"{'≥' if active else '<'} threshold {s.threshold:.0f} → LED {'ON' if active else 'OFF'}."
    )
    res["sensor"] = {"value": value, "threshold": s.threshold, "active": active}
    return res


# ---------------------------------------------------------------- public
def solve(circuit: Circuit, **kwargs) -> Dict[str, Any]:
    """Universal entry point — dispatch on circuit type."""
    dispatch = {
        "series": _solve_series,
        "parallel": _solve_divider_with_load,
        "rc": _solve_rc,
        "digital": _solve_series,
        "transistor_switch": _solve_transistor_switch,
        "sensor_threshold": _solve_sensor_threshold,
    }
    fn = dispatch.get(circuit.ctype, _solve_series)
    if circuit.ctype == "sensor_threshold":
        return fn(circuit, kwargs.get("sensor_value"))
    return fn(circuit)


# Backward-compatible v1 API
def solve_series_circuit(circuit) -> Dict[str, Any]:
    return _solve_series(circuit)
