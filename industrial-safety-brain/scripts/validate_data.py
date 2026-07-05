"""
validate_data.py — Post-generation validation for all datasets.

Checks:
1. No duplicate IDs in any dataset
2. All timestamps are valid ISO-8601
3. Equipment belongs to its correct zone
4. Permit start_time < end_time
5. Shift timings don't overlap within the same zone + same shift name
"""

import json
import os
import sys
from datetime import datetime

from plant_config import EQUIPMENT_TO_ZONE

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets")

# Track overall pass/fail
_errors: list = []
_passed: int = 0


def _log_error(dataset: str, detail: str) -> None:
    _errors.append(f"  [FAIL] [{dataset}] {detail}")


def _log_pass(check: str) -> None:
    global _passed
    _passed += 1
    print(f"  [PASS] {check}")


def _load_json(subdir: str, filename: str) -> list:
    path = os.path.join(DATASETS_DIR, subdir, filename)
    if not os.path.exists(path):
        print(f"  [WARN] File not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _check_no_duplicate_ids(data: list, id_field: str, dataset_name: str) -> None:
    """Ensure no duplicate IDs exist."""
    ids = [r[id_field] for r in data]
    dupes = set(x for x in ids if ids.count(x) > 1)
    if dupes:
        _log_error(dataset_name, f"Duplicate IDs: {dupes}")
    else:
        _log_pass(f"{dataset_name}: no duplicate {id_field}s ({len(ids)} records)")


def _check_valid_timestamps(data: list, fields: list, dataset_name: str) -> None:
    """Ensure all timestamp fields parse as valid ISO-8601."""
    bad = 0
    for record in data:
        for field_name in fields:
            val = record.get(field_name)
            if val is None:
                continue
            try:
                datetime.fromisoformat(val)
            except (ValueError, TypeError):
                bad += 1
                first_key = list(record.keys())[0]
                _log_error(dataset_name, f"Invalid timestamp: {field_name}={val} in {record.get(first_key, '?')}")
    if bad == 0:
        _log_pass(f"{dataset_name}: all timestamps valid")


def _check_equipment_zone(data: list, dataset_name: str) -> None:
    """Ensure equipment belongs to the zone it's assigned to."""
    mismatches = 0
    for record in data:
        equip = record.get("equipment")
        zone = record.get("zone")
        if equip and zone:
            expected_zone = EQUIPMENT_TO_ZONE.get(equip)
            if expected_zone and expected_zone != zone:
                mismatches += 1
                _log_error(
                    dataset_name,
                    f"Equipment {equip} in {zone} but belongs to {expected_zone}"
                )
    if mismatches == 0:
        _log_pass(f"{dataset_name}: all equipment in correct zones")


def _check_permit_times(data: list) -> None:
    """Ensure permit start_time < end_time."""
    bad = 0
    for record in data:
        start = record.get("start_time")
        end = record.get("end_time")
        if start and end:
            if datetime.fromisoformat(start) >= datetime.fromisoformat(end):
                bad += 1
                _log_error("permits", f"{record['permit_id']}: start >= end")
    if bad == 0:
        _log_pass("permits: all start_time < end_time")


def _check_shift_overlaps(data: list) -> None:
    """Check that shifts of the same name in the same zone on the same day don't overlap."""
    from collections import defaultdict

    # Group by (zone, shift_name, date)
    groups = defaultdict(list)
    for record in data:
        start = datetime.fromisoformat(record["start_time"])
        key = (record["zone"], record["shift_name"], start.date().isoformat())
        groups[key].append(record)

    overlaps = 0
    for key, shifts in groups.items():
        if len(shifts) > 1:
            overlaps += 1
            _log_error(
                "shifts",
                f"Duplicate shift: zone={key[0]}, shift={key[1]}, date={key[2]} ({len(shifts)} entries)"
            )

    if overlaps == 0:
        _log_pass("shifts: no duplicate shifts within same zone/day")


def validate_all() -> bool:
    """Run all validations. Returns True if all pass."""
    global _errors, _passed
    _errors = []
    _passed = 0

    print()
    print("=" * 46)
    print("  Dataset Validation Report")
    print("=" * 46)
    print()

    # -- Sensors --
    print("--- Sensors ---")
    sensors = _load_json("sensors", "sensors.json")
    if sensors:
        _check_no_duplicate_ids(sensors, "sensor_id", "sensors")
        _check_valid_timestamps(sensors, ["timestamp"], "sensors")
        _check_equipment_zone(sensors, "sensors")

    # -- Permits --
    print("\n--- Permits ---")
    permits = _load_json("permits", "permits.json")
    if permits:
        _check_no_duplicate_ids(permits, "permit_id", "permits")
        _check_valid_timestamps(permits, ["start_time", "end_time"], "permits")
        _check_equipment_zone(permits, "permits")
        _check_permit_times(permits)

    # -- Maintenance --
    print("\n--- Maintenance ---")
    maintenance = _load_json("maintenance", "maintenance.json")
    if maintenance:
        _check_no_duplicate_ids(maintenance, "maintenance_id", "maintenance")
        _check_valid_timestamps(maintenance, ["scheduled_time", "completion_time"], "maintenance")
        _check_equipment_zone(maintenance, "maintenance")

    # -- Shifts --
    print("\n--- Shifts ---")
    shifts = _load_json("shifts", "shifts.json")
    if shifts:
        _check_no_duplicate_ids(shifts, "shift_id", "shifts")
        _check_valid_timestamps(shifts, ["start_time", "end_time"], "shifts")
        _check_shift_overlaps(shifts)

    # -- Incidents --
    print("\n--- Incidents ---")
    incidents = _load_json("incidents", "incidents.json")
    if incidents:
        _check_no_duplicate_ids(incidents, "incident_id", "incidents")
        _check_valid_timestamps(incidents, ["date"], "incidents")
        _check_equipment_zone(incidents, "incidents")

    # -- Summary --
    print(f"\n{'=' * 46}")
    if _errors:
        print(f"  FAILED -- {len(_errors)} error(s), {_passed} check(s) passed\n")
        for err in _errors:
            print(err)
        return False
    else:
        print(f"  ALL PASSED -- {_passed} check(s)")
        return True


def main() -> None:
    success = validate_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
