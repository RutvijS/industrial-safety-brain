"""
plant_state_models.py -- Pydantic models for the Unified Plant State Layer.

These models aggregate data from all 5 datasets into a single contextual
view per zone, designed for consumption by future modules (Risk Engine,
RAG, Knowledge Graph, Safety Copilot, Dashboard, etc.).
"""

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

from app.models.data_models import (
    Incident,
    MaintenanceRecord,
    Permit,
    SensorReading,
    Shift,
)


class SensorSummary(BaseModel):
    """Aggregated sensor status for a zone."""

    total_readings: int = 0
    normal_count: int = 0
    warning_count: int = 0
    critical_count: int = 0
    avg_gas_level: float = 0.0
    avg_temperature: float = 0.0
    avg_pressure: float = 0.0
    avg_humidity: float = 0.0
    avg_vibration: float = 0.0
    latest_readings: List[SensorReading] = Field(
        default_factory=list,
        description="Most recent sensor readings (up to 10)",
    )


class EquipmentContext(BaseModel):
    """Equipment with its associated data across all datasets."""

    equipment_name: str
    zone: str
    latest_sensor: Optional[SensorReading] = None
    active_permits: List[Permit] = Field(default_factory=list)
    active_maintenance: List[MaintenanceRecord] = Field(default_factory=list)
    recent_incidents: List[Incident] = Field(default_factory=list)


class OverallContext(BaseModel):
    """Derived context for a zone -- high-level operational summary."""

    worker_count: int = 0
    high_risk_operations: int = Field(
        default=0,
        description="Count of active Hot Work + Confined Space permits",
    )
    hazard_level: str = Field(
        default="Low",
        description="Low / Moderate / High / Critical -- derived from sensor status",
    )
    active_permit_count: int = 0
    active_maintenance_count: int = 0
    critical_sensor_count: int = 0


class ZoneState(BaseModel):
    """Complete state for a single zone -- the core Plant State unit."""

    zone: str
    zone_name: str
    risk_type: str
    description: str
    current_sensor_status: SensorSummary
    active_permits: List[Permit] = Field(default_factory=list)
    active_maintenance: List[MaintenanceRecord] = Field(default_factory=list)
    current_shift: Optional[Shift] = None
    recent_incidents: List[Incident] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)
    equipment_details: List[EquipmentContext] = Field(default_factory=list)
    overall_context: OverallContext = Field(default_factory=OverallContext)


class PlantState(BaseModel):
    """Complete state of the entire plant -- all zones combined."""

    zones: List[ZoneState]
    generated_at: str = Field(
        description="ISO-8601 timestamp of when this state was computed",
    )


class PlantOverviewSummary(BaseModel):
    """High-level summary counts across the entire plant."""

    zone_count: int = 0
    active_permits: int = 0
    maintenance_jobs: int = 0
    critical_sensors: int = 0
    warning_sensors: int = 0
    recent_incidents: int = 0
    total_workers_on_shift: int = 0
    hazard_summary: Dict[str, str] = Field(
        default_factory=dict,
        description="Zone -> hazard level mapping",
    )
