"""
risk_config.py -- Configuration for the Compound Risk Detection Engine.

All weights, thresholds, and compound rule definitions live here.
Nothing is hardcoded inside the engine.
"""

from typing import Dict, List, Tuple

# ─────────────────────────────────────────────────────────────
# Factor Weights (must sum to 100)
# ─────────────────────────────────────────────────────────────

FACTOR_WEIGHTS: Dict[str, float] = {
    "gas_level": 30.0,
    "temperature": 15.0,
    "pressure": 15.0,
    "permit_risk": 20.0,
    "maintenance_risk": 10.0,
    "shift_risk": 5.0,
    "incident_history": 5.0,
}

# ─────────────────────────────────────────────────────────────
# Sensor Thresholds
# ─────────────────────────────────────────────────────────────

# (warning_threshold, critical_threshold)
SENSOR_THRESHOLDS: Dict[str, Tuple[float, float]] = {
    "gas_level": (50.0, 100.0),         # ppm
    "temperature": (80.0, 150.0),       # Celsius
    "pressure": (6.0, 10.0),            # bar
    "humidity": (75.0, 90.0),           # percent
    "vibration": (7.0, 12.0),           # mm/s
}

# ─────────────────────────────────────────────────────────────
# Risk Score Thresholds
# ─────────────────────────────────────────────────────────────

RISK_LEVELS: List[Tuple[int, str]] = [
    (80, "CRITICAL"),
    (60, "HIGH"),
    (40, "MEDIUM"),
    (0, "LOW"),
]

HAZARD_LEVELS: List[Tuple[int, str]] = [
    (80, "Very High"),
    (60, "High"),
    (40, "Moderate"),
    (20, "Low"),
    (0, "Very Low"),
]

# ─────────────────────────────────────────────────────────────
# Compound Risk Rules
#
# Each rule defines:
#   name:        Human-readable name
#   conditions:  List of condition functions (take ZoneState, return bool)
#   severity:    Resulting severity if all conditions match
#   score_boost: Additional score points added when this compound fires
#   description: What makes this combination dangerous
# ─────────────────────────────────────────────────────────────

# Condition helper keys -- the engine maps these to actual checks
# This keeps the config declarative while the engine handles evaluation.

COMPOUND_RULES: List[Dict] = [
    {
        "name": "Gas Leak + Hot Work",
        "condition_keys": ["high_gas", "hot_work_active"],
        "severity": "Critical",
        "score_boost": 25,
        "description": "Elevated gas levels combined with active hot work permits create an explosion risk.",
    },
    {
        "name": "Gas Leak + Confined Space Entry",
        "condition_keys": ["high_gas", "confined_space_active"],
        "severity": "Critical",
        "score_boost": 25,
        "description": "High gas concentration during confined space entry risks asphyxiation or toxic exposure.",
    },
    {
        "name": "High Pressure + Valve Maintenance",
        "condition_keys": ["high_pressure", "valve_maintenance_active"],
        "severity": "High",
        "score_boost": 15,
        "description": "Performing valve maintenance while pressure is elevated risks blowout or steam release.",
    },
    {
        "name": "Maintenance + Night Shift + Recent Incident",
        "condition_keys": ["maintenance_active", "night_shift", "recent_similar_incident"],
        "severity": "High",
        "score_boost": 15,
        "description": "Maintenance during night shift with recent incident history increases human error probability.",
    },
    {
        "name": "Chemical Storage + Temperature Rise",
        "condition_keys": ["chemical_zone", "high_temperature"],
        "severity": "Critical",
        "score_boost": 20,
        "description": "Rising temperatures in chemical storage areas risk exothermic reactions or vapor release.",
    },
    {
        "name": "Boiler Maintenance + Pressure Increase",
        "condition_keys": ["boiler_zone", "high_pressure", "maintenance_active"],
        "severity": "High",
        "score_boost": 15,
        "description": "Boiler maintenance during pressure surges risks steam burns or vessel failure.",
    },
    {
        "name": "High Vibration + Equipment Maintenance",
        "condition_keys": ["high_vibration", "maintenance_active"],
        "severity": "Medium",
        "score_boost": 10,
        "description": "High vibration during maintenance indicates equipment instability -- injury risk.",
    },
    {
        "name": "Multiple Critical Sensors",
        "condition_keys": ["multiple_critical_sensors"],
        "severity": "Critical",
        "score_boost": 20,
        "description": "Multiple sensors in critical state indicate a cascading failure scenario.",
    },
    {
        "name": "High Worker Density + Hazardous Operations",
        "condition_keys": ["high_worker_count", "high_risk_operations"],
        "severity": "High",
        "score_boost": 10,
        "description": "High worker density during hazardous operations amplifies potential casualty count.",
    },
    {
        "name": "Overdue Maintenance + Critical Sensors",
        "condition_keys": ["overdue_maintenance", "any_critical_sensor"],
        "severity": "High",
        "score_boost": 15,
        "description": "Overdue maintenance on equipment showing critical readings indicates neglected safety.",
    },
]

# ─────────────────────────────────────────────────────────────
# Compound risk multiplier range
# ─────────────────────────────────────────────────────────────

# When compound risks are detected, the base score is multiplied
COMPOUND_MULTIPLIER_MIN = 1.0   # No compound risks
COMPOUND_MULTIPLIER_MAX = 1.5   # Many compound risks

# ─────────────────────────────────────────────────────────────
# Confidence calculation
# ─────────────────────────────────────────────────────────────

# Base confidence starts at this value
BASE_CONFIDENCE = 70

# Each supporting evidence item adds this much confidence (capped at 99)
CONFIDENCE_PER_EVIDENCE = 3

# ─────────────────────────────────────────────────────────────
# High-risk permit types
# ─────────────────────────────────────────────────────────────

HIGH_RISK_PERMIT_TYPES = {"Hot Work", "Confined Space Entry"}

# ─────────────────────────────────────────────────────────────
# Gemini explanation prompt template
# ─────────────────────────────────────────────────────────────

GEMINI_EXPLANATION_PROMPT = """You are an industrial safety expert. Analyze this risk assessment and provide a clear, actionable explanation.

RISK ASSESSMENT DATA:
Zone: {zone}
Overall Risk Level: {risk_level}
Risk Score: {risk_score}/100
Hazard Level: {hazard_level}

DETECTED COMPOUND RISKS:
{detected_risks}

RISK FACTORS:
{risk_factors}

SUPPORTING EVIDENCE:
{evidence}

Provide your response in this EXACT format:

SUMMARY:
[2-3 sentence overview of the situation]

WHY THIS IS DANGEROUS:
[Explain why this combination of factors creates danger]

RECOMMENDED ACTIONS:
1. [Most urgent action]
2. [Second priority action]
3. [Third priority action]

PRIORITY: [IMMEDIATE / HIGH / MEDIUM / LOW]

POSSIBLE CONSEQUENCES:
[What could happen if no action is taken]

Keep your response factual. Do NOT invent sensor values. Only reference data provided above."""
