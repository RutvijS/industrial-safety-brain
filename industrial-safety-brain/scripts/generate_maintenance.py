"""
generate_maintenance.py — Generates ~100 realistic maintenance records.

Correlations:
- Equipment stays in its correct zone
- Boiler maintenance → Zone B
- Emergency maintenance has faster completion
- Remarks are type-appropriate
"""

import json
import os
import random
from datetime import datetime, timedelta

from plant_config import (
    EQUIPMENT,
    MAINTENANCE_REMARKS,
    MAINTENANCE_TYPES,
    RANDOM_SEED,
    WORKERS,
    ZONES,
)

random.seed(RANDOM_SEED)

NUM_RECORDS = 100
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets", "maintenance")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "maintenance.json")

BASE_TIME = datetime(2025, 6, 1, 0, 0, 0)
TIME_SPAN_DAYS = 30

MAINTENANCE_STATUSES = ["Completed", "Completed", "Completed", "In Progress",
                         "Scheduled", "Overdue", "Cancelled"]


def _maintenance_times(m_type: str) -> tuple:
    """Generate scheduled and completion times based on maintenance type."""
    day_offset = random.randint(0, TIME_SPAN_DAYS - 1)
    hour = random.randint(6, 22)
    scheduled = BASE_TIME + timedelta(days=day_offset, hours=hour)

    if m_type == "Emergency":
        duration = timedelta(hours=random.uniform(1, 4))
    elif m_type == "Inspection":
        duration = timedelta(hours=random.uniform(1, 3))
    elif m_type == "Preventive":
        duration = timedelta(hours=random.uniform(2, 8))
    else:  # Corrective
        duration = timedelta(hours=random.uniform(3, 12))

    completion = scheduled + duration
    return scheduled.isoformat(), completion.isoformat()


def generate_maintenance() -> list:
    """Generate ~100 maintenance records with zone-equipment consistency."""
    records = []
    zones = list(ZONES.keys())

    for i in range(NUM_RECORDS):
        zone = random.choice(zones)
        equipment = random.choice(EQUIPMENT[zone])
        m_type = random.choice(MAINTENANCE_TYPES)
        engineer = random.choice(WORKERS[zone])
        status = random.choice(MAINTENANCE_STATUSES)
        scheduled, completion = _maintenance_times(m_type)
        remarks = random.choice(MAINTENANCE_REMARKS[m_type])

        # If status is Scheduled or Cancelled, no completion time
        if status in ("Scheduled", "Cancelled", "In Progress"):
            completion = None

        records.append({
            "maintenance_id": f"MNT-{i + 1:04d}",
            "equipment": equipment,
            "zone": zone,
            "maintenance_type": m_type,
            "assigned_engineer": engineer["name"],
            "status": status,
            "scheduled_time": scheduled,
            "completion_time": completion,
            "remarks": remarks,
        })

    records.sort(key=lambda r: r["scheduled_time"])
    return records


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    data = generate_maintenance()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Generated {len(data)} maintenance records -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
