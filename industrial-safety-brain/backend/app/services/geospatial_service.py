"""
geospatial_service.py -- Geospatial Safety Intelligence Service.

Transforms existing backend data into frontend-friendly geospatial structures.

IMPORTANT: This service does NOT calculate risk.
The Risk Engine remains the single source of truth.
This service only reads existing data and formats it for visualization.

Architecture:
    PlantStateService -> RiskEngine -> GeospatialService -> Frontend Heatmap
"""

from datetime import datetime
from typing import Dict, List

from app.models.geospatial_models import (
    HeatmapData,
    HeatmapZone,
    PlantLayout,
    ZoneDetails,
    ZoneLayout,
)
from app.services.plant_state_service import (
    ZONE_METADATA,
    VALID_ZONES,
    plant_state_service,
)
from app.services.risk_engine import risk_engine


# ── Plant Layout Definition ─────────────────────────────────
# Static spatial positions for the 4 zones on the plant map.
# These represent a realistic industrial layout grid.

ZONE_LAYOUTS: Dict[str, Dict] = {
    "Zone A": {"id": "A", "x": 40,  "y": 40,  "width": 280, "height": 200},
    "Zone B": {"id": "B", "x": 360, "y": 40,  "width": 280, "height": 200},
    "Zone C": {"id": "C", "x": 40,  "y": 280, "width": 280, "height": 200},
    "Zone D": {"id": "D", "x": 360, "y": 280, "width": 280, "height": 200},
}

# ── Color Mapping ───────────────────────────────────────────

RISK_COLORS: Dict[str, str] = {
    "CRITICAL": "#ef4444",
    "HIGH": "#f97316",
    "MEDIUM": "#eab308",
    "LOW": "#22c55e",
}


class GeospatialService:
    """Transforms plant data into geospatial visualization structures.

    Never calculates risk. Only reads from PlantStateService and RiskEngine.
    """

    def get_plant_layout(self) -> PlantLayout:
        """Return the static plant layout with zone positions."""
        zones = []
        for zone_key, layout in ZONE_LAYOUTS.items():
            meta = ZONE_METADATA.get(zone_key, {})
            zones.append(ZoneLayout(
                id=layout["id"],
                name=meta.get("zone_name", zone_key),
                x=layout["x"],
                y=layout["y"],
                width=layout["width"],
                height=layout["height"],
                risk_type=meta.get("risk_type", ""),
                description=meta.get("description", ""),
            ))

        return PlantLayout(zones=zones)

    def get_heatmap_data(self) -> HeatmapData:
        """Generate heatmap data by reading existing risk assessments.

        Fetches plant state, runs risk analysis (deterministic),
        and maps results to heatmap zones with colors.
        """
        heatmap_zones: List[HeatmapZone] = []
        worst_score = 0
        worst_level = "LOW"

        for zone_key in VALID_ZONES:
            try:
                # Get zone state from PlantStateService
                zone_state = plant_state_service.get_zone_state(zone_key)

                # Get risk assessment from RiskEngine (deterministic, no Gemini)
                assessment = risk_engine.analyze_zone(zone_state)

                risk_level = assessment.overall_risk
                risk_score = assessment.risk_score
                color = RISK_COLORS.get(risk_level, "#22c55e")

                heatmap_zones.append(HeatmapZone(
                    zone=zone_key,
                    zone_name=zone_state.zone_name,
                    risk_score=risk_score,
                    risk_level=risk_level,
                    color=color,
                    hazard_level=assessment.hazard_level,
                    active_permits=len(zone_state.active_permits),
                    active_maintenance=len(zone_state.active_maintenance),
                    recent_incidents=len(zone_state.recent_incidents),
                    avg_temperature=zone_state.current_sensor_status.avg_temperature,
                    avg_gas_level=zone_state.current_sensor_status.avg_gas_level,
                    avg_pressure=zone_state.current_sensor_status.avg_pressure,
                    compound_risks=len(assessment.detected_compound_risks),
                    worker_count=zone_state.overall_context.worker_count,
                ))

                if risk_score > worst_score:
                    worst_score = risk_score
                    worst_level = risk_level

            except Exception:
                # Zone unavailable -- add placeholder
                heatmap_zones.append(HeatmapZone(
                    zone=zone_key,
                    zone_name=ZONE_METADATA.get(zone_key, {}).get("zone_name", zone_key),
                    risk_score=0,
                    risk_level="LOW",
                    color="#22c55e",
                ))

        return HeatmapData(
            zones=heatmap_zones,
            overall_risk=worst_level,
            overall_risk_score=worst_score,
            timestamp=datetime.utcnow().isoformat(),
        )

    def get_zone_details(self, zone_key: str) -> ZoneDetails:
        """Get comprehensive zone details for the side panel.

        Combines plant state + risk assessment into a single view.
        """
        if zone_key not in VALID_ZONES:
            raise ValueError(f"Unknown zone: {zone_key}")

        meta = ZONE_METADATA.get(zone_key, {})
        zone_state = plant_state_service.get_zone_state(zone_key)
        assessment = risk_engine.analyze_zone(zone_state)

        return ZoneDetails(
            zone=zone_key,
            zone_name=meta.get("zone_name", zone_key),
            risk_type=meta.get("risk_type", ""),
            description=meta.get("description", ""),
            avg_temperature=zone_state.current_sensor_status.avg_temperature,
            avg_gas_level=zone_state.current_sensor_status.avg_gas_level,
            avg_pressure=zone_state.current_sensor_status.avg_pressure,
            avg_humidity=zone_state.current_sensor_status.avg_humidity,
            avg_vibration=zone_state.current_sensor_status.avg_vibration,
            critical_sensors=zone_state.current_sensor_status.critical_count,
            warning_sensors=zone_state.current_sensor_status.warning_count,
            risk_score=assessment.risk_score,
            risk_level=assessment.overall_risk,
            hazard_level=assessment.hazard_level,
            confidence=assessment.confidence,
            detected_risks=[
                {"name": r.name, "severity": r.severity, "description": r.description}
                for r in assessment.detected_compound_risks
            ],
            recommendations=[
                {"priority": r.priority, "action": r.action, "reasoning": r.reasoning}
                for r in assessment.recommended_actions
            ],
            risk_factors=[
                {
                    "name": f.name,
                    "raw_value": f.raw_value,
                    "normalized_score": f.normalized_score,
                    "status": f.status,
                }
                for f in assessment.risk_factors
            ],
            active_permits=len(zone_state.active_permits),
            active_maintenance=len(zone_state.active_maintenance),
            recent_incidents=len(zone_state.recent_incidents),
            worker_count=zone_state.overall_context.worker_count,
        )


# Singleton
geospatial_service = GeospatialService()
