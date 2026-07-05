"""
generate_permits.py — Generates ~100 realistic work permits.

Correlations:
- Hot Work permits → mostly Zone C (65%)
- Confined Space Entry → mostly Zone A (60%)
- Electrical Isolation → mostly Zone B (50%)
- Maintenance permits → evenly distributed
"""

import json
import os
import random
from datetime import datetime, timedelta

from plant_config import (
    EQUIPMENT,
    PERMIT_TYPES,
    RANDOM_SEED,
    SUPERVISORS,
    WORKERS,
    ZONES,
)

random.seed(RANDOM_SEED)

NUM_RECORDS = 100
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets", "permits")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "permits.json")

BASE_TIME = datetime(2025, 6, 1, 6, 0, 0)
TIME_SPAN_DAYS = 30

PERMIT_STATUSES = ["Approved", "Approved", "Approved", "Closed", "Closed",
                    "Expired", "Revoked", "Pending"]


def _pick_zone_for_permit(permit_type: str) -> str:
    """Choose a zone biased by the permit type's primary zone."""
    config = PERMIT_TYPES[permit_type]
    zones = list(ZONES.keys())

    if config["primary_zone"] and random.random() < config["primary_weight"]:
        return config["primary_zone"]
    return random.choice(zones)


def _random_permit_window() -> tuple:
    """Generate a realistic start_time and end_time (2–8 hour window)."""
    day_offset = random.randint(0, TIME_SPAN_DAYS - 1)
    start_hour = random.choice([6, 7, 8, 9, 10, 14, 15, 16, 22, 23])
    duration_hours = random.randint(2, 8)

    start = BASE_TIME + timedelta(days=day_offset, hours=start_hour - 6)
    end = start + timedelta(hours=duration_hours)
    return start.isoformat(), end.isoformat()


def generate_permits() -> list:
    """Generate ~100 work permits with zone-biased distribution."""
    records = []
    permit_type_names = list(PERMIT_TYPES.keys())

    for i in range(NUM_RECORDS):
        permit_type = random.choice(permit_type_names)
        zone = _pick_zone_for_permit(permit_type)
        equipment = random.choice(EQUIPMENT[zone])
        worker = random.choice(WORKERS[zone])
        supervisor = SUPERVISORS[zone]
        start_time, end_time = _random_permit_window()
        status = random.choice(PERMIT_STATUSES)

        records.append({
            "permit_id": f"PTW-{i + 1:04d}",
            "permit_type": permit_type,
            "zone": zone,
            "equipment": equipment,
            "issued_to": worker["name"],
            "approved_by": supervisor["name"],
            "start_time": start_time,
            "end_time": end_time,
            "status": status,
        })

    records.sort(key=lambda r: r["start_time"])
    return records


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    data = generate_permits()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Generated {len(data)} permit records -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
