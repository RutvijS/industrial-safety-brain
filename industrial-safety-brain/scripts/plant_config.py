"""
plant_config.py — Central source of truth for the virtual industrial plant.

Every generator imports this module to ensure cross-dataset consistency.
Zones, equipment, workers, supervisors, shifts, value ranges, and
correlation rules are all defined here.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# ─────────────────────────────────────────────────────────────
# Random seed for reproducibility
# ─────────────────────────────────────────────────────────────
RANDOM_SEED = 42

# ─────────────────────────────────────────────────────────────
# Zones
# ─────────────────────────────────────────────────────────────

ZONES = {
    "Zone A": {
        "name": "Coke Oven Area",
        "risk_type": "High Gas Risk",
        "description": "Coke oven batteries and by-product recovery. High concentration of CO, methane, and volatile gases.",
    },
    "Zone B": {
        "name": "Boiler House",
        "risk_type": "High Temperature",
        "description": "Industrial boilers, steam generation, and heat exchangers. Extreme temperatures and high-pressure steam.",
    },
    "Zone C": {
        "name": "Maintenance Workshop",
        "risk_type": "Frequent Hot Work",
        "description": "Welding bays, grinding stations, and repair workshops. Frequent hot work permits required.",
    },
    "Zone D": {
        "name": "Chemical Storage",
        "risk_type": "Hazardous Chemicals",
        "description": "Bulk chemical storage tanks, acid handling, and solvent drums. Risk of spills and toxic exposure.",
    },
}

# ─────────────────────────────────────────────────────────────
# Equipment per zone
# ─────────────────────────────────────────────────────────────

EQUIPMENT: Dict[str, List[str]] = {
    "Zone A": [
        "Gas Line G101",
        "Gas Line G102",
        "Compressor C101",
        "Exhaust Fan EF101",
        "Valve V101",
        "Valve V102",
        "Pump P101",
        "Sensor Array SA101",
    ],
    "Zone B": [
        "Boiler B301",
        "Boiler B302",
        "Steam Turbine ST301",
        "Heat Exchanger HX301",
        "Pump P201",
        "Valve V201",
        "Valve V202",
        "Pressure Relief PRV301",
    ],
    "Zone C": [
        "Welding Unit WU401",
        "Welding Unit WU402",
        "Grinding Machine GM401",
        "Lathe Machine LM401",
        "Crane CR401",
        "Compressor C201",
        "Exhaust Fan EF401",
        "Tool Cabinet TC401",
    ],
    "Zone D": [
        "Tank T401",
        "Tank T402",
        "Tank T403",
        "Pump P301",
        "Valve V301",
        "Valve V302",
        "Spill Containment SC401",
        "Ventilation Unit VU401",
    ],
}

# Reverse lookup: equipment_id → zone
EQUIPMENT_TO_ZONE: Dict[str, str] = {}
for zone, items in EQUIPMENT.items():
    for item in items:
        EQUIPMENT_TO_ZONE[item] = zone

# ─────────────────────────────────────────────────────────────
# Workers and Supervisors
# ─────────────────────────────────────────────────────────────

SUPERVISORS = {
    "Zone A": {"id": "SUP-A01", "name": "Rajesh Kumar"},
    "Zone B": {"id": "SUP-B01", "name": "Anand Sharma"},
    "Zone C": {"id": "SUP-C01", "name": "Vikram Singh"},
    "Zone D": {"id": "SUP-D01", "name": "Priya Nair"},
}

WORKERS: Dict[str, List[Dict[str, str]]] = {
    "Zone A": [
        {"id": "WRK-A01", "name": "Amit Patel"},
        {"id": "WRK-A02", "name": "Suresh Yadav"},
        {"id": "WRK-A03", "name": "Deepak Verma"},
        {"id": "WRK-A04", "name": "Ramesh Gupta"},
        {"id": "WRK-A05", "name": "Sanjay Tiwari"},
    ],
    "Zone B": [
        {"id": "WRK-B01", "name": "Manoj Dubey"},
        {"id": "WRK-B02", "name": "Arun Mishra"},
        {"id": "WRK-B03", "name": "Kiran Reddy"},
        {"id": "WRK-B04", "name": "Naveen Joshi"},
        {"id": "WRK-B05", "name": "Ravi Shankar"},
    ],
    "Zone C": [
        {"id": "WRK-C01", "name": "Prakash Mehra"},
        {"id": "WRK-C02", "name": "Sunil Kumar"},
        {"id": "WRK-C03", "name": "Ajay Pandey"},
        {"id": "WRK-C04", "name": "Vinod Saxena"},
        {"id": "WRK-C05", "name": "Rohit Chauhan"},
    ],
    "Zone D": [
        {"id": "WRK-D01", "name": "Nitin Agarwal"},
        {"id": "WRK-D02", "name": "Santosh Mishra"},
        {"id": "WRK-D03", "name": "Gaurav Bhatt"},
        {"id": "WRK-D04", "name": "Hemant Jha"},
        {"id": "WRK-D05", "name": "Pankaj Srivastava"},
    ],
}

# ─────────────────────────────────────────────────────────────
# Shifts
# ─────────────────────────────────────────────────────────────

SHIFT_DEFINITIONS = [
    {"shift_id": "SHIFT-M", "shift_name": "Morning",  "start_hour": 6,  "end_hour": 14},
    {"shift_id": "SHIFT-E", "shift_name": "Evening",  "start_hour": 14, "end_hour": 22},
    {"shift_id": "SHIFT-N", "shift_name": "Night",    "start_hour": 22, "end_hour": 6},
]

# ─────────────────────────────────────────────────────────────
# Sensor value ranges — (normal_min, normal_max, danger_min, danger_max)
# ─────────────────────────────────────────────────────────────

@dataclass
class SensorProfile:
    """Defines normal and dangerous ranges for each sensor metric in a zone."""
    gas_level: Tuple[float, float, float, float]       # ppm
    temperature: Tuple[float, float, float, float]     # °C
    pressure: Tuple[float, float, float, float]        # bar
    humidity: Tuple[float, float, float, float]        # %
    vibration: Tuple[float, float, float, float]       # mm/s


SENSOR_PROFILES: Dict[str, SensorProfile] = {
    "Zone A": SensorProfile(
        gas_level=(5.0, 25.0, 80.0, 150.0),       # Coke oven — high gas baseline
        temperature=(40.0, 80.0, 120.0, 200.0),
        pressure=(1.0, 3.0, 5.0, 8.0),
        humidity=(30.0, 60.0, 15.0, 25.0),         # Low humidity in danger
        vibration=(0.5, 3.0, 6.0, 12.0),
    ),
    "Zone B": SensorProfile(
        gas_level=(1.0, 10.0, 30.0, 60.0),
        temperature=(80.0, 150.0, 200.0, 350.0),   # Boiler — very high temps
        pressure=(5.0, 15.0, 20.0, 35.0),          # Boiler — high pressure
        humidity=(40.0, 70.0, 20.0, 35.0),
        vibration=(1.0, 4.0, 8.0, 15.0),
    ),
    "Zone C": SensorProfile(
        gas_level=(1.0, 8.0, 20.0, 50.0),
        temperature=(25.0, 45.0, 60.0, 120.0),     # Workshop — moderate
        pressure=(1.0, 2.5, 4.0, 6.0),
        humidity=(35.0, 65.0, 20.0, 30.0),
        vibration=(2.0, 6.0, 10.0, 20.0),          # Machinery vibration
    ),
    "Zone D": SensorProfile(
        gas_level=(2.0, 15.0, 40.0, 100.0),        # Chemical vapors
        temperature=(15.0, 30.0, 40.0, 60.0),      # Storage — cool
        pressure=(1.0, 2.0, 3.5, 6.0),
        humidity=(40.0, 75.0, 80.0, 95.0),          # High humidity = danger
        vibration=(0.2, 1.5, 3.0, 6.0),
    ),
}

# ─────────────────────────────────────────────────────────────
# Permit types and their primary zones
# ─────────────────────────────────────────────────────────────

PERMIT_TYPES = {
    "Hot Work": {
        "primary_zone": "Zone C",
        "primary_weight": 0.65,
        "description": "Welding, cutting, grinding, or brazing operations",
    },
    "Confined Space Entry": {
        "primary_zone": "Zone A",
        "primary_weight": 0.60,
        "description": "Entry into vessels, tanks, silos, or enclosed spaces",
    },
    "Electrical Isolation": {
        "primary_zone": "Zone B",
        "primary_weight": 0.50,
        "description": "Lockout/tagout for electrical maintenance",
    },
    "Maintenance": {
        "primary_zone": None,
        "primary_weight": 0.0,
        "description": "General maintenance activities",
    },
}

# ─────────────────────────────────────────────────────────────
# Maintenance types
# ─────────────────────────────────────────────────────────────

MAINTENANCE_TYPES = ["Preventive", "Corrective", "Emergency", "Inspection"]

MAINTENANCE_REMARKS = {
    "Preventive": [
        "Routine lubrication completed",
        "Filter replacement as per schedule",
        "Calibration check performed",
        "Belt tension adjusted",
        "Gasket inspection — no wear detected",
        "Scheduled overhaul completed within SLA",
    ],
    "Corrective": [
        "Bearing replaced due to excessive wear",
        "Seal leakage fixed — root cause: aging gasket",
        "Motor winding repaired",
        "Control valve actuator replaced",
        "Thermocouple recalibrated after drift detected",
    ],
    "Emergency": [
        "Emergency shutdown triggered — pressure spike",
        "Gas leak isolated and patched",
        "Electrical fault cleared — breaker replaced",
        "Steam line rupture — welded and pressure tested",
        "Pump seizure — impeller replaced under emergency protocol",
    ],
    "Inspection": [
        "Visual inspection — no anomalies",
        "Ultrasonic thickness measurement within limits",
        "Vibration analysis — slight increase noted, monitoring",
        "Thermal imaging — hot spot detected on junction box",
        "Corrosion mapping completed — 2mm wall loss in 12 months",
    ],
}

# ─────────────────────────────────────────────────────────────
# Incident templates — zone-appropriate
# ─────────────────────────────────────────────────────────────

INCIDENT_TEMPLATES = [
    # Zone A — Gas risks
    {
        "zone": "Zone A",
        "types": [
            {
                "description": "CO gas leak detected near coke oven battery",
                "root_cause": "Corroded gas line fitting",
                "corrective_action": "Replaced corroded section, installed inline gas monitor",
                "lessons_learned": "Implement quarterly corrosion inspection on all gas lines",
                "related_regulation": "OSHA 1910.146 — Permit-Required Confined Spaces",
            },
            {
                "description": "Methane accumulation in coke oven by-product area",
                "root_cause": "Exhaust fan failure during night shift",
                "corrective_action": "Replaced exhaust fan motor, added redundant ventilation",
                "lessons_learned": "Critical ventilation systems require redundant backups",
                "related_regulation": "OSHA 1910.106 — Flammable Liquids",
            },
            {
                "description": "Worker exposed to toxic fumes in confined space",
                "root_cause": "Inadequate atmospheric testing before entry",
                "corrective_action": "Revised confined space entry SOP, mandatory 4-gas monitor",
                "lessons_learned": "Never enter confined space without real-time gas monitoring",
                "related_regulation": "OSHA 1910.146 — Permit-Required Confined Spaces",
            },
            {
                "description": "Explosion in coke oven gas line during maintenance",
                "root_cause": "Residual gas in line not fully purged before hot work",
                "corrective_action": "Mandatory gas-free certificate before any hot work on gas lines",
                "lessons_learned": "Double-check purge completion with portable gas detector",
                "related_regulation": "OSHA 1910.252 — Welding, Cutting and Brazing",
            },
        ],
    },
    # Zone B — Temperature / Pressure
    {
        "zone": "Zone B",
        "types": [
            {
                "description": "Boiler pressure surge exceeding safety threshold",
                "root_cause": "Pressure relief valve stuck in closed position",
                "corrective_action": "Replaced PRV, added redundant pressure sensor with auto-shutdown",
                "lessons_learned": "PRV testing must occur monthly, not quarterly",
                "related_regulation": "OSHA 1910.217 — Mechanical Power Presses",
            },
            {
                "description": "Steam line rupture in boiler house causing burns",
                "root_cause": "Wall thinning due to erosion-corrosion not detected in last inspection",
                "corrective_action": "Emergency weld repair, updated NDE inspection schedule",
                "lessons_learned": "High-velocity steam lines need annual ultrasonic thickness checks",
                "related_regulation": "OSHA 1910.169 — Air Receivers",
            },
            {
                "description": "Heat exchanger tube failure causing cross-contamination",
                "root_cause": "Stress corrosion cracking under high-temperature cycling",
                "corrective_action": "Replaced tube bundle, upgraded metallurgy to Inconel",
                "lessons_learned": "Material selection must account for thermal cycling fatigue",
                "related_regulation": "ASME BPVC Section VIII — Pressure Vessels",
            },
            {
                "description": "Pump mechanical seal failure causing hot oil leak",
                "root_cause": "Seal ran dry during brief loss of cooling water",
                "corrective_action": "Installed seal flush system with low-flow alarm",
                "lessons_learned": "All hot-service pumps require seal flush monitoring",
                "related_regulation": "OSHA 1910.106 — Flammable Liquids",
            },
        ],
    },
    # Zone C — Hot Work
    {
        "zone": "Zone C",
        "types": [
            {
                "description": "Fire ignition during welding near flammable material",
                "root_cause": "Welding sparks ignited solvent-soaked rags stored nearby",
                "corrective_action": "Enforced 35-ft hot work perimeter, fire watch extended to 1 hour",
                "lessons_learned": "Remove all flammable materials before issuing hot work permit",
                "related_regulation": "OSHA 1910.252 — Welding, Cutting and Brazing",
            },
            {
                "description": "Electrical short circuit in welding unit causing arc flash",
                "root_cause": "Damaged insulation on welding cable not detected in pre-use check",
                "corrective_action": "Replaced all welding cables, added monthly cable inspection",
                "lessons_learned": "Visual cable inspection before every shift is mandatory",
                "related_regulation": "OSHA 1910.303 — Electrical General Requirements",
            },
            {
                "description": "Crane load drop during equipment repositioning",
                "root_cause": "Worn sling not replaced as per schedule",
                "corrective_action": "Replaced all slings, implemented color-coded quarterly inspection tags",
                "lessons_learned": "Lifting equipment inspection must be strictly time-bound",
                "related_regulation": "OSHA 1910.184 — Slings",
            },
            {
                "description": "Grinding wheel disintegration causing fragment injury",
                "root_cause": "Grinding wheel exceeded maximum RPM due to incorrect machine setting",
                "corrective_action": "Installed RPM limiters, mandatory ring test before wheel mounting",
                "lessons_learned": "Never exceed manufacturer RPM rating on abrasive wheels",
                "related_regulation": "OSHA 1910.215 — Abrasive Wheel Machinery",
            },
        ],
    },
    # Zone D — Chemical
    {
        "zone": "Zone D",
        "types": [
            {
                "description": "Sulfuric acid spill from storage tank overflow",
                "root_cause": "Level indicator malfunction, tank overfilled during transfer",
                "corrective_action": "Installed redundant level sensor with high-high alarm and auto-shutoff",
                "lessons_learned": "All chemical transfers require operator presence and backup alarms",
                "related_regulation": "OSHA 1910.120 — Hazardous Waste Operations",
            },
            {
                "description": "Chemical vapor release in storage area causing evacuation",
                "root_cause": "Incompatible chemicals stored in adjacent bays reacted through slow leak",
                "corrective_action": "Redesigned storage layout per chemical compatibility matrix",
                "lessons_learned": "Chemical segregation must follow NFPA 400 compatibility guidelines",
                "related_regulation": "OSHA 1910.1200 — Hazard Communication",
            },
            {
                "description": "Worker chemical burn from valve leak during transfer",
                "root_cause": "Valve packing worn, no drip tray in place",
                "corrective_action": "Replaced all valve packings, installed drip trays under all transfer points",
                "lessons_learned": "PPE compliance and drip containment are non-negotiable during transfers",
                "related_regulation": "OSHA 1910.132 — Personal Protective Equipment",
            },
            {
                "description": "Solvent drum explosion in chemical storage during hot weather",
                "root_cause": "Direct sunlight exposure caused pressure buildup in sealed drum",
                "corrective_action": "Relocated drum storage to shaded area, installed pressure relief bungs",
                "lessons_learned": "Volatile chemical storage must be temperature-controlled",
                "related_regulation": "OSHA 1910.106 — Flammable Liquids",
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────
# Severity levels for incidents
# ─────────────────────────────────────────────────────────────

SEVERITY_LEVELS = ["Minor", "Moderate", "Serious", "Critical", "Fatal"]
SEVERITY_WEIGHTS = [0.30, 0.30, 0.20, 0.15, 0.05]
