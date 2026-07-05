"""
generate_shifts.py — Generates shift schedules for all zones.

Structure:
- Morning (06:00–14:00), Evening (14:00–22:00), Night (22:00–06:00)
- Each zone has its own supervisor and worker pool
- 30 days of shifts across 4 zones = 360 records
"""

import json
import os
import random
from datetime import datetime, timedelta

from plant_config import (
    RANDOM_SEED,
    SHIFT_DEFINITIONS,
    SUPERVISORS,
    WORKERS,
    ZONES,
)

random.seed(RANDOM_SEED)

NUM_DAYS = 30
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets", "shifts")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "shifts.json")

BASE_DATE = datetime(2025, 6, 1)


def generate_shifts() -> list:
    """Generate shift records: 3 shifts × 4 zones × 30 days."""
    records = []
    shift_counter = 0

    for day in range(NUM_DAYS):
        current_date = BASE_DATE + timedelta(days=day)

        for zone in ZONES:
            supervisor = SUPERVISORS[zone]
            zone_workers = WORKERS[zone]

            for shift_def in SHIFT_DEFINITIONS:
                shift_counter += 1

                # Calculate start and end times
                start_hour = shift_def["start_hour"]
                end_hour = shift_def["end_hour"]

                start_time = current_date.replace(hour=start_hour, minute=0, second=0)

                if end_hour < start_hour:
                    # Night shift crosses midnight
                    end_time = (current_date + timedelta(days=1)).replace(
                        hour=end_hour, minute=0, second=0
                    )
                else:
                    end_time = current_date.replace(hour=end_hour, minute=0, second=0)

                # Assign 3–4 workers per shift (realistic crew size)
                num_workers = random.randint(3, min(4, len(zone_workers)))
                assigned = random.sample(zone_workers, num_workers)

                records.append({
                    "shift_id": f"SHF-{shift_counter:04d}",
                    "shift_name": shift_def["shift_name"],
                    "supervisor": supervisor["name"],
                    "supervisor_id": supervisor["id"],
                    "workers": [w["name"] for w in assigned],
                    "worker_ids": [w["id"] for w in assigned],
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "zone": zone,
                })

    records.sort(key=lambda r: (r["start_time"], r["zone"]))
    return records


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    data = generate_shifts()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Generated {len(data)} shift records -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
