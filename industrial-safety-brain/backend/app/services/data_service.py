"""
data_service.py -- Service layer for reading and filtering plant datasets.

Architecture: Route -> Service -> JSON Dataset
- Reads each JSON file once and caches in memory
- All filtering logic lives here, not in routes
- Handles missing files and invalid JSON gracefully
"""

import json
import os
from typing import Any, Dict, List, Optional

from app.models.data_models import (
    Incident,
    MaintenanceRecord,
    Permit,
    SensorReading,
    Shift,
)

# Path to datasets directory (relative to project root)
DATASETS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "datasets"
)


class DataService:
    """Reads JSON datasets and provides filtered access.

    Data is loaded once on first access and cached in memory.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, List[dict]] = {}

    def _load_dataset(self, subdir: str, filename: str) -> List[dict]:
        """Load a JSON dataset file, caching the result."""
        cache_key = f"{subdir}/{filename}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        filepath = os.path.join(DATASETS_DIR, subdir, filename)
        filepath = os.path.normpath(filepath)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Dataset not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._cache[cache_key] = data
        return data

    @staticmethod
    def _apply_filters(data: List[dict], filters: Dict[str, Optional[str]]) -> List[dict]:
        """Filter records by matching field values (case-insensitive contains)."""
        result = data
        for field, value in filters.items():
            if value is not None:
                value_lower = value.lower()
                result = [
                    r for r in result
                    if field in r and r[field] is not None
                    and value_lower in str(r[field]).lower()
                ]
        return result

    # ── Public API ───────────────────────────────────────────

    def get_sensors(
        self,
        zone: Optional[str] = None,
        status: Optional[str] = None,
        equipment: Optional[str] = None,
    ) -> List[SensorReading]:
        raw = self._load_dataset("sensors", "sensors.json")
        filtered = self._apply_filters(raw, {
            "zone": zone, "status": status, "equipment": equipment,
        })
        return [SensorReading(**r) for r in filtered]

    def get_permits(
        self,
        zone: Optional[str] = None,
        status: Optional[str] = None,
        permit_type: Optional[str] = None,
    ) -> List[Permit]:
        raw = self._load_dataset("permits", "permits.json")
        filtered = self._apply_filters(raw, {
            "zone": zone, "status": status, "permit_type": permit_type,
        })
        return [Permit(**r) for r in filtered]

    def get_maintenance(
        self,
        zone: Optional[str] = None,
        status: Optional[str] = None,
        equipment: Optional[str] = None,
        maintenance_type: Optional[str] = None,
    ) -> List[MaintenanceRecord]:
        raw = self._load_dataset("maintenance", "maintenance.json")
        filtered = self._apply_filters(raw, {
            "zone": zone, "status": status,
            "equipment": equipment, "maintenance_type": maintenance_type,
        })
        return [MaintenanceRecord(**r) for r in filtered]

    def get_shifts(
        self,
        zone: Optional[str] = None,
        shift_name: Optional[str] = None,
    ) -> List[Shift]:
        raw = self._load_dataset("shifts", "shifts.json")
        filtered = self._apply_filters(raw, {
            "zone": zone, "shift_name": shift_name,
        })
        return [Shift(**r) for r in filtered]

    def get_incidents(
        self,
        zone: Optional[str] = None,
        severity: Optional[str] = None,
        equipment: Optional[str] = None,
    ) -> List[Incident]:
        raw = self._load_dataset("incidents", "incidents.json")
        filtered = self._apply_filters(raw, {
            "zone": zone, "severity": severity, "equipment": equipment,
        })
        return [Incident(**r) for r in filtered]


# Singleton instance
data_service = DataService()
