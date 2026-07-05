"""
data_models.py -- Pydantic models for all plant datasets.

Each model matches the exact JSON shape produced by the Phase 2A generators.
"""

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import List, Optional


# ── Sensor Reading ──────────────────────────────────────────

class SensorReading(BaseModel):
    sensor_id: str
    timestamp: str
    zone: str
    equipment: str
    gas_level: float
    temperature: float
    pressure: float
    humidity: float
    vibration: float
    status: str


# ── Permit ──────────────────────────────────────────────────

class Permit(BaseModel):
    permit_id: str
    permit_type: str
    zone: str
    equipment: str
    issued_to: str
    approved_by: str
    start_time: str
    end_time: str
    status: str


# ── Maintenance Record ─────────────────────────────────────

class MaintenanceRecord(BaseModel):
    maintenance_id: str
    equipment: str
    zone: str
    maintenance_type: str
    assigned_engineer: str
    status: str
    scheduled_time: str
    completion_time: Optional[str] = None
    remarks: str


# ── Shift ───────────────────────────────────────────────────

class Shift(BaseModel):
    shift_id: str
    shift_name: str
    supervisor: str
    supervisor_id: str
    workers: List[str]
    worker_ids: List[str]
    start_time: str
    end_time: str
    zone: str


# ── Incident ───────────────────────────────────────────────

class Incident(BaseModel):
    incident_id: str
    date: str
    zone: str
    equipment: str
    description: str
    root_cause: str
    severity: str
    injuries: int
    corrective_action: str
    lessons_learned: str
    related_regulation: str
