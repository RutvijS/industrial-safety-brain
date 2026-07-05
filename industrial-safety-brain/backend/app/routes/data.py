"""
data.py -- REST endpoints for plant datasets.

Architecture: Route -> DataService -> JSON files
Each endpoint supports optional query parameters for filtering.
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.models.data_models import (
    Incident,
    MaintenanceRecord,
    Permit,
    SensorReading,
    Shift,
)
from app.services.data_service import data_service

router = APIRouter(tags=["Plant Data"])


@router.get("/sensors", response_model=List[SensorReading])
async def get_sensors(
    zone: Optional[str] = Query(None, description="Filter by zone (e.g. Zone A)"),
    status: Optional[str] = Query(None, description="Filter by status (Normal, Warning, Critical)"),
    equipment: Optional[str] = Query(None, description="Filter by equipment name"),
) -> List[SensorReading]:
    """Return all sensor readings, optionally filtered."""
    try:
        return data_service.get_sensors(zone=zone, status=status, equipment=equipment)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load sensor data: {e}")


@router.get("/permits", response_model=List[Permit])
async def get_permits(
    zone: Optional[str] = Query(None, description="Filter by zone"),
    status: Optional[str] = Query(None, description="Filter by status (Approved, Closed, Pending, etc.)"),
    permit_type: Optional[str] = Query(None, description="Filter by permit type (Hot Work, etc.)"),
) -> List[Permit]:
    """Return all work permits, optionally filtered."""
    try:
        return data_service.get_permits(zone=zone, status=status, permit_type=permit_type)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load permit data: {e}")


@router.get("/maintenance", response_model=List[MaintenanceRecord])
async def get_maintenance(
    zone: Optional[str] = Query(None, description="Filter by zone"),
    status: Optional[str] = Query(None, description="Filter by status"),
    equipment: Optional[str] = Query(None, description="Filter by equipment"),
    maintenance_type: Optional[str] = Query(None, description="Filter by type (Preventive, Corrective, etc.)"),
) -> List[MaintenanceRecord]:
    """Return all maintenance records, optionally filtered."""
    try:
        return data_service.get_maintenance(
            zone=zone, status=status,
            equipment=equipment, maintenance_type=maintenance_type,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load maintenance data: {e}")


@router.get("/shifts", response_model=List[Shift])
async def get_shifts(
    zone: Optional[str] = Query(None, description="Filter by zone"),
    shift_name: Optional[str] = Query(None, description="Filter by shift (Morning, Evening, Night)"),
) -> List[Shift]:
    """Return all shift schedules, optionally filtered."""
    try:
        return data_service.get_shifts(zone=zone, shift_name=shift_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load shift data: {e}")


@router.get("/incidents", response_model=List[Incident])
async def get_incidents(
    zone: Optional[str] = Query(None, description="Filter by zone"),
    severity: Optional[str] = Query(None, description="Filter by severity (Minor, Moderate, Serious, Critical, Fatal)"),
    equipment: Optional[str] = Query(None, description="Filter by equipment"),
) -> List[Incident]:
    """Return all historical incidents, optionally filtered."""
    try:
        return data_service.get_incidents(zone=zone, severity=severity, equipment=equipment)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load incident data: {e}")
