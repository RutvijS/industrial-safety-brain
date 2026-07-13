"""
geospatial.py -- REST endpoints for Geospatial Safety Intelligence.

GET /plant-layout          - Static plant zone layout
GET /heatmap               - Live heatmap data (risk-colored zones)
GET /zone-details/{zone}   - Comprehensive zone details for side panel

These endpoints do NOT calculate risk.
They read from the existing Risk Engine and Plant State.
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException

from app.models.geospatial_models import HeatmapData, PlantLayout, ZoneDetails
from app.services.geospatial_service import geospatial_service
from app.services.plant_state_service import VALID_ZONES

router = APIRouter(tags=["Geospatial Intelligence"])


@router.get("/plant-layout", response_model=PlantLayout)
async def get_plant_layout() -> PlantLayout:
    """Return the static plant layout with zone positions and metadata."""
    return geospatial_service.get_plant_layout()


@router.get("/heatmap", response_model=HeatmapData)
async def get_heatmap() -> HeatmapData:
    """Return live heatmap data for all zones.

    Each zone includes risk_score, risk_level, color, and operational counts.
    Data is read from the existing Risk Engine -- no risk calculation here.
    """
    try:
        return geospatial_service.get_heatmap_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Heatmap generation failed: {e}")


@router.get("/zone-details/{zone}", response_model=ZoneDetails)
async def get_zone_details(zone: str) -> ZoneDetails:
    """Return comprehensive details for a single zone.

    Combines plant state + risk assessment for the side panel view.
    """
    if zone not in VALID_ZONES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown zone: {zone}. Valid zones: {VALID_ZONES}",
        )
    try:
        return geospatial_service.get_zone_details(zone)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Zone details failed: {e}")
