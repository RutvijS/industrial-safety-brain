"""
plant_state_service.py -- Unified Plant State Layer.

Merges all 5 isolated datasets into a single contextual state per zone.
Uses DataService for all data reading -- never reads JSON files directly.

Architecture:
    Route -> PlantStateService -> DataService -> JSON datasets

This service is the single source of truth for all future modules:
Risk Engine, RAG, Knowledge Graph, Safety Copilot, Dashboard, etc.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.models.data_models import (
    Incident,
    MaintenanceRecord,
    Permit,
    SensorReading,
    Shift,
)
from app.models.plant_state_models import (
    EquipmentContext,
    OverallContext,
    PlantOverviewSummary,
    PlantState,
    SensorSummary,
    ZoneState,
)
from app.services.data_service import data_service


# ── Zone metadata (mirrors scripts/plant_config.py without importing it) ──

ZONE_METADATA: Dict[str, Dict[str, str]] = {
    "Zone A": {
        "zone_name": "Coke Oven Area",
        "risk_type": "High Gas Risk",
        "description": "Coke oven batteries and by-product recovery. High concentration of CO, methane, and volatile gases.",
    },
    "Zone B": {
        "zone_name": "Boiler House",
        "risk_type": "High Temperature",
        "description": "Industrial boilers, steam generation, and heat exchangers. Extreme temperatures and high-pressure steam.",
    },
    "Zone C": {
        "zone_name": "Maintenance Workshop",
        "risk_type": "Frequent Hot Work",
        "description": "Welding bays, grinding stations, and repair workshops. Frequent hot work permits required.",
    },
    "Zone D": {
        "zone_name": "Chemical Storage",
        "risk_type": "Hazardous Chemicals",
        "description": "Bulk chemical storage tanks, acid handling, and solvent drums. Risk of spills and toxic exposure.",
    },
}

VALID_ZONES = list(ZONE_METADATA.keys())

# Permit statuses that count as "active"
ACTIVE_PERMIT_STATUSES = {"Approved", "Pending"}

# Maintenance statuses that count as "active"
ACTIVE_MAINTENANCE_STATUSES = {"In Progress", "Scheduled", "Overdue"}

# High-risk permit types
HIGH_RISK_PERMIT_TYPES = {"Hot Work", "Confined Space Entry"}

# How many recent incidents to include per zone
RECENT_INCIDENT_LIMIT = 10

# How many latest sensor readings to include per zone
LATEST_SENSOR_LIMIT = 10


# ── Helper functions (reusable, not hardcoded) ──────────────

def _filter_by_zone(records: list, zone: str, zone_field: str = "zone") -> list:
    """Filter any list of Pydantic models by zone."""
    return [r for r in records if getattr(r, zone_field, None) == zone]


def _filter_active_permits(permits: List[Permit]) -> List[Permit]:
    """Return permits with active statuses."""
    return [p for p in permits if p.status in ACTIVE_PERMIT_STATUSES]


def _filter_active_maintenance(records: List[MaintenanceRecord]) -> List[MaintenanceRecord]:
    """Return maintenance records with active statuses."""
    return [m for m in records if m.status in ACTIVE_MAINTENANCE_STATUSES]


def _get_latest_shift(shifts: List[Shift]) -> Optional[Shift]:
    """Return the most recent shift (by start_time)."""
    if not shifts:
        return None
    return max(shifts, key=lambda s: s.start_time)


def _get_recent_incidents(incidents: List[Incident], limit: int = RECENT_INCIDENT_LIMIT) -> List[Incident]:
    """Return the most recent incidents, sorted by date descending."""
    sorted_incidents = sorted(incidents, key=lambda i: i.date, reverse=True)
    return sorted_incidents[:limit]


def _compute_sensor_summary(sensors: List[SensorReading]) -> SensorSummary:
    """Aggregate sensor readings into a summary."""
    if not sensors:
        return SensorSummary()

    normal = sum(1 for s in sensors if s.status == "Normal")
    warning = sum(1 for s in sensors if s.status == "Warning")
    critical = sum(1 for s in sensors if s.status == "Critical")
    total = len(sensors)

    latest = sorted(sensors, key=lambda s: s.timestamp, reverse=True)[:LATEST_SENSOR_LIMIT]

    return SensorSummary(
        total_readings=total,
        normal_count=normal,
        warning_count=warning,
        critical_count=critical,
        avg_gas_level=round(sum(s.gas_level for s in sensors) / total, 2),
        avg_temperature=round(sum(s.temperature for s in sensors) / total, 2),
        avg_pressure=round(sum(s.pressure for s in sensors) / total, 2),
        avg_humidity=round(sum(s.humidity for s in sensors) / total, 2),
        avg_vibration=round(sum(s.vibration for s in sensors) / total, 2),
        latest_readings=latest,
    )


def _compute_hazard_level(sensor_summary: SensorSummary) -> str:
    """Derive hazard level from sensor status counts."""
    if sensor_summary.critical_count > 0:
        return "Critical"
    if sensor_summary.warning_count > 3:
        return "High"
    if sensor_summary.warning_count > 0:
        return "Moderate"
    return "Low"


def _count_high_risk_operations(permits: List[Permit]) -> int:
    """Count active permits that are high-risk (Hot Work, Confined Space)."""
    return sum(1 for p in permits if p.permit_type in HIGH_RISK_PERMIT_TYPES)


def _get_zone_equipment(zone: str, sensors: List[SensorReading]) -> List[str]:
    """Infer equipment list from sensor readings for a zone."""
    equipment_set = set()
    for s in sensors:
        if s.zone == zone:
            equipment_set.add(s.equipment)
    return sorted(equipment_set)


def _build_equipment_context(
    equipment_name: str,
    zone: str,
    sensors: List[SensorReading],
    permits: List[Permit],
    maintenance: List[MaintenanceRecord],
    incidents: List[Incident],
) -> EquipmentContext:
    """Build context for a single piece of equipment across all datasets."""
    eq_sensors = [s for s in sensors if s.equipment == equipment_name]
    latest_sensor = max(eq_sensors, key=lambda s: s.timestamp) if eq_sensors else None

    eq_permits = [p for p in permits if p.equipment == equipment_name]
    eq_maintenance = [m for m in maintenance if m.equipment == equipment_name]
    eq_incidents = [i for i in incidents if i.equipment == equipment_name]

    return EquipmentContext(
        equipment_name=equipment_name,
        zone=zone,
        latest_sensor=latest_sensor,
        active_permits=eq_permits,
        active_maintenance=eq_maintenance,
        recent_incidents=eq_incidents[:5],
    )


# ── Main Service ────────────────────────────────────────────

class PlantStateService:
    """Merges all datasets into unified zone-level state objects.

    Delegates all data reading to DataService. All correlation and
    relationship-building logic lives here.
    """

    def get_zone_state(self, zone: str) -> ZoneState:
        """Build the complete state for a single zone."""
        if zone not in ZONE_METADATA:
            raise ValueError(f"Unknown zone: {zone}. Valid zones: {VALID_ZONES}")

        meta = ZONE_METADATA[zone]

        # Fetch zone-scoped data from DataService
        sensors = data_service.get_sensors(zone=zone)
        permits = data_service.get_permits(zone=zone)
        maintenance = data_service.get_maintenance(zone=zone)
        shifts = data_service.get_shifts(zone=zone)
        incidents = data_service.get_incidents(zone=zone)

        # Compute derived state
        active_permits = _filter_active_permits(permits)
        active_maintenance = _filter_active_maintenance(maintenance)
        current_shift = _get_latest_shift(shifts)
        recent_incidents = _get_recent_incidents(incidents)
        sensor_summary = _compute_sensor_summary(sensors)
        hazard_level = _compute_hazard_level(sensor_summary)

        # Equipment list and details
        equipment_names = _get_zone_equipment(zone, sensors)
        equipment_details = [
            _build_equipment_context(eq, zone, sensors, active_permits, active_maintenance, recent_incidents)
            for eq in equipment_names
        ]

        # Worker count from current shift
        worker_count = len(current_shift.workers) if current_shift else 0

        overall = OverallContext(
            worker_count=worker_count,
            high_risk_operations=_count_high_risk_operations(active_permits),
            hazard_level=hazard_level,
            active_permit_count=len(active_permits),
            active_maintenance_count=len(active_maintenance),
            critical_sensor_count=sensor_summary.critical_count,
        )

        return ZoneState(
            zone=zone,
            zone_name=meta["zone_name"],
            risk_type=meta["risk_type"],
            description=meta["description"],
            current_sensor_status=sensor_summary,
            active_permits=active_permits,
            active_maintenance=active_maintenance,
            current_shift=current_shift,
            recent_incidents=recent_incidents,
            equipment=equipment_names,
            equipment_details=equipment_details,
            overall_context=overall,
        )

    def get_plant_state(self) -> PlantState:
        """Build the complete state for all zones."""
        zones = [self.get_zone_state(z) for z in VALID_ZONES]
        return PlantState(
            zones=zones,
            generated_at=datetime.utcnow().isoformat(),
        )

    def get_plant_overview(self) -> PlantOverviewSummary:
        """Build a high-level summary across the entire plant."""
        plant = self.get_plant_state()

        total_active_permits = sum(z.overall_context.active_permit_count for z in plant.zones)
        total_maintenance = sum(z.overall_context.active_maintenance_count for z in plant.zones)
        total_critical = sum(z.overall_context.critical_sensor_count for z in plant.zones)
        total_warning = sum(z.current_sensor_status.warning_count for z in plant.zones)
        total_incidents = sum(len(z.recent_incidents) for z in plant.zones)
        total_workers = sum(z.overall_context.worker_count for z in plant.zones)
        hazard_map = {z.zone: z.overall_context.hazard_level for z in plant.zones}

        return PlantOverviewSummary(
            zone_count=len(plant.zones),
            active_permits=total_active_permits,
            maintenance_jobs=total_maintenance,
            critical_sensors=total_critical,
            warning_sensors=total_warning,
            recent_incidents=total_incidents,
            total_workers_on_shift=total_workers,
            hazard_summary=hazard_map,
        )


# Singleton instance
plant_state_service = PlantStateService()
