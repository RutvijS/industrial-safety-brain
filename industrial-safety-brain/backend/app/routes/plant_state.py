"""
plant_state.py -- REST endpoints for the Unified Plant State Layer.

Architecture: Route -> PlantStateService -> DataService -> JSON datasets
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from typing import List

from app.models.plant_state_models import (
    PlantOverviewSummary,
    PlantState,
    ZoneState,
)
from app.services.plant_state_service import plant_state_service

router = APIRouter(tags=["Plant State"])


@router.get("/plant-state", response_model=PlantState)
async def get_plant_state() -> PlantState:
    """Return the complete unified state for all zones."""
    try:
        return plant_state_service.get_plant_state()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build plant state: {e}")


@router.get("/plant-state/{zone}", response_model=ZoneState)
async def get_zone_state(zone: str) -> ZoneState:
    """Return the unified state for a single zone."""
    try:
        return plant_state_service.get_zone_state(zone)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build zone state: {e}")


@router.get("/plant-overview", response_model=PlantOverviewSummary)
async def get_plant_overview() -> PlantOverviewSummary:
    """Return high-level summary counts across the entire plant."""
    try:
        return plant_state_service.get_plant_overview()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build plant overview: {e}")
