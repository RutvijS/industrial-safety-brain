"""
generate_all.py — Master script that runs all generators and then validates.

Usage:
    py scripts/generate_all.py
"""

import importlib
import sys
import time


def main() -> None:
    print("=" * 46)
    print("  Industrial Safety Brain -- Data Generator")
    print("=" * 46)
    print()

    generators = [
        ("Sensor Data", "generate_sensor_data"),
        ("Work Permits", "generate_permits"),
        ("Maintenance Records", "generate_maintenance"),
        ("Shift Schedules", "generate_shifts"),
        ("Historical Incidents", "generate_incidents"),
    ]

    start = time.time()

    for label, module_name in generators:
        print(f"-- Generating {label}...")
        mod = importlib.import_module(module_name)
        mod.main()

    elapsed = time.time() - start
    print(f"\n[OK] All datasets generated in {elapsed:.2f}s\n")

    # Run validation
    print("-- Running validation...")
    from validate_data import validate_all
    success = validate_all()

    if not success:
        print("\n[WARN] Some validations failed. Check errors above.")
        sys.exit(1)
    else:
        print("\n[OK] All done. Datasets are ready.")
        sys.exit(0)


if __name__ == "__main__":
    main()
