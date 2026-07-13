"""
geospatial_models.py -- Pydantic models for the Geospatial Safety Intelligence module.

These models transform backend data into frontend-friendly structures.
They do NOT calculate risk -- they only represent existing data spatially.
"""

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class ZoneLayout(BaseModel):
    """Spatial layout of a single plant zone."""

    id: str = Field(description="Zone identifier (A, B, C, D)")
    name: str = Field(description="Zone name (e.g. Coke Oven Area)")
    x: int = Field(description="X coordinate on the plant map")
    y: int = Field(description="Y coordinate on the plant map")
    width: int = Field(description="Width of the zone area")
    height: int = Field(description="Height of the zone area")
    risk_type: str = Field(default="", description="Zone risk category")
    description: str = Field(default="")


class PlantLayout(BaseModel):
    """Complete plant layout with all zones."""

    plant_name: str = "Steel Plant Alpha"
    total_zones: int = 4
    zones: List[ZoneLayout] = Field(default_factory=list)


class HeatmapZone(BaseModel):
    """Heatmap data for a single zone -- color-coded by risk."""

    zone: str
    zone_name: str = ""
    risk_score: int = 0
    risk_level: str = "LOW"
    color: str = "#22c55e"
    hazard_level: str = "Very Low"
    active_permits: int = 0
    active_maintenance: int = 0
    recent_incidents: int = 0
    avg_temperature: float = 0.0
    avg_gas_level: float = 0.0
    avg_pressure: float = 0.0
    compound_risks: int = 0
    worker_count: int = 0


class HeatmapData(BaseModel):
    """Complete heatmap data for the entire plant."""

    zones: List[HeatmapZone] = Field(default_factory=list)
    overall_risk: str = "LOW"
    overall_risk_score: int = 0
    timestamp: str = ""


class ZoneDetails(BaseModel):
    """Detailed information for a single zone (plant state + risk + intelligence)."""

    zone: str
    zone_name: str = ""
    risk_type: str = ""
    description: str = ""

    # Sensor summary
    avg_temperature: float = 0.0
    avg_gas_level: float = 0.0
    avg_pressure: float = 0.0
    avg_humidity: float = 0.0
    avg_vibration: float = 0.0
    critical_sensors: int = 0
    warning_sensors: int = 0

    # Risk assessment
    risk_score: int = 0
    risk_level: str = "LOW"
    hazard_level: str = "Very Low"
    confidence: int = 0
    detected_risks: List[Dict] = Field(default_factory=list)
    recommendations: List[Dict] = Field(default_factory=list)
    risk_factors: List[Dict] = Field(default_factory=list)

    # Operations
    active_permits: int = 0
    active_maintenance: int = 0
    recent_incidents: int = 0
    worker_count: int = 0

    # Intelligence (from RAG if available)
    has_intelligence: bool = False
    similar_incidents_count: int = 0
    lessons_learned_count: int = 0
    supporting_docs_count: int = 0
