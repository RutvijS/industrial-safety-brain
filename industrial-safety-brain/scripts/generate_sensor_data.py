"""
generate_sensor_data.py — Generates ~500 realistic sensor readings.

Correlations:
- Zone A: high gas → elevated temperature
- Zone B: boilers → high pressure and temperature
- Zone C: machinery → higher vibration
- Zone D: chemicals → gas from vapors, humidity matters
- ~15% of records are dangerous conditions
"""

import json
import os
import random
from datetime import datetime, timedelta

from plant_config import (
    EQUIPMENT,
    RANDOM_SEED,
    SENSOR_PROFILES,
    ZONES,
)

random.seed(RANDOM_SEED)

NUM_RECORDS = 500
DANGER_RATIO = 0.15  # ~15% dangerous readings
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets", "sensors")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "sensors.json")

# Time window: last 30 days
BASE_TIME = datetime(2025, 6, 1, 0, 0, 0)
TIME_SPAN_HOURS = 30 * 24  # 30 days


def _random_timestamp() -> str:
    """Generate a random ISO-8601 timestamp within the last 30 days."""
    offset = timedelta(hours=random.uniform(0, TIME_SPAN_HOURS))
    return (BASE_TIME + offset).isoformat()


def _sample_value(range_tuple: tuple, is_danger: bool) -> float:
    """Sample a value from either the normal or danger range."""
    if is_danger:
        lo, hi = range_tuple[2], range_tuple[3]
    else:
        lo, hi = range_tuple[0], range_tuple[1]
    return round(random.uniform(lo, hi), 2)


def _determine_status(is_danger: bool, gas: float, temp: float, pressure: float) -> str:
    """Derive sensor status from readings."""
    if not is_danger:
        return "Normal"
    # Graduated danger levels
    if gas > 100 or temp > 250 or pressure > 25:
        return "Critical"
    return "Warning"


def generate_sensor_data() -> list:
    """Generate ~500 sensor records with realistic correlations."""
    records = []
    zones = list(ZONES.keys())

    for i in range(NUM_RECORDS):
        zone = random.choice(zones)
        equipment = random.choice(EQUIPMENT[zone])
        profile = SENSOR_PROFILES[zone]
        is_danger = random.random() < DANGER_RATIO

        gas = _sample_value(profile.gas_level, is_danger)
        temp = _sample_value(profile.temperature, is_danger)
        pressure = _sample_value(profile.pressure, is_danger)
        humidity = _sample_value(profile.humidity, is_danger)
        vibration = _sample_value(profile.vibration, is_danger)

        # Correlation: if gas is dangerously high, push temperature up too
        if is_danger and gas > profile.gas_level[2] * 0.8:
            temp = max(temp, temp * random.uniform(1.05, 1.25))
            temp = round(temp, 2)

        # Correlation: boiler zone danger → pressure spike
        if zone == "Zone B" and is_danger:
            pressure = max(pressure, pressure * random.uniform(1.1, 1.3))
            pressure = round(pressure, 2)

        status = _determine_status(is_danger, gas, temp, pressure)

        records.append({
            "sensor_id": f"SEN-{i + 1:04d}",
            "timestamp": _random_timestamp(),
            "zone": zone,
            "equipment": equipment,
            "gas_level": gas,
            "temperature": temp,
            "pressure": pressure,
            "humidity": humidity,
            "vibration": vibration,
            "status": status,
        })

    # Sort by timestamp for realism
    records.sort(key=lambda r: r["timestamp"])
    return records


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    data = generate_sensor_data()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Generated {len(data)} sensor records -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
