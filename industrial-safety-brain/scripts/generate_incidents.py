"""
generate_incidents.py — Generates ~50 realistic historical incidents.

Correlations:
- Gas leaks / explosions → Zone A
- Pressure surges / boiler failures → Zone B
- Hot work fires / electrical shorts → Zone C
- Chemical spills / vapor releases → Zone D
- Some incidents linked to shift changes (06:00, 14:00, 22:00)
- Some incidents linked to maintenance gaps
- Severity distribution weighted (most minor/moderate, few fatal)
"""

import json
import os
import random
from datetime import datetime, timedelta

from plant_config import (
    EQUIPMENT,
    INCIDENT_TEMPLATES,
    RANDOM_SEED,
    SEVERITY_LEVELS,
    SEVERITY_WEIGHTS,
)

random.seed(RANDOM_SEED)

NUM_RECORDS = 50
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets", "incidents")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "incidents.json")

BASE_TIME = datetime(2024, 1, 1)
TIME_SPAN_DAYS = 545  # ~18 months of historical data

# Shift-change hours — incidents more likely during handover
SHIFT_CHANGE_HOURS = [6, 14, 22]
SHIFT_CHANGE_PROBABILITY = 0.25  # 25% of incidents happen near shift change

# Injury counts by severity
INJURY_RANGES = {
    "Minor": (0, 1),
    "Moderate": (0, 2),
    "Serious": (1, 3),
    "Critical": (2, 5),
    "Fatal": (1, 3),
}


def _pick_severity() -> str:
    """Weighted severity selection."""
    return random.choices(SEVERITY_LEVELS, weights=SEVERITY_WEIGHTS, k=1)[0]


def _incident_timestamp() -> str:
    """Generate an incident timestamp, biased toward shift-change hours."""
    day_offset = random.randint(0, TIME_SPAN_DAYS)
    date = BASE_TIME + timedelta(days=day_offset)

    if random.random() < SHIFT_CHANGE_PROBABILITY:
        hour = random.choice(SHIFT_CHANGE_HOURS) + random.choice([-1, 0, 0, 1])
        hour = hour % 24
    else:
        hour = random.randint(0, 23)

    minute = random.randint(0, 59)
    return date.replace(hour=hour, minute=minute).isoformat()


def generate_incidents() -> list:
    """Generate ~50 historical incidents with zone-appropriate types."""
    records = []

    # Flatten all templates into a pool with zone tags
    template_pool = []
    for zone_group in INCIDENT_TEMPLATES:
        zone = zone_group["zone"]
        for t in zone_group["types"]:
            template_pool.append({"zone": zone, **t})

    for i in range(NUM_RECORDS):
        template = random.choice(template_pool)
        zone = template["zone"]
        equipment = random.choice(EQUIPMENT[zone])
        severity = _pick_severity()
        injuries = random.randint(*INJURY_RANGES[severity])
        timestamp = _incident_timestamp()

        records.append({
            "incident_id": f"INC-{i + 1:04d}",
            "date": timestamp,
            "zone": zone,
            "equipment": equipment,
            "description": template["description"],
            "root_cause": template["root_cause"],
            "severity": severity,
            "injuries": injuries,
            "corrective_action": template["corrective_action"],
            "lessons_learned": template["lessons_learned"],
            "related_regulation": template["related_regulation"],
        })

    records.sort(key=lambda r: r["date"])
    return records


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    data = generate_incidents()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Generated {len(data)} incident records -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
