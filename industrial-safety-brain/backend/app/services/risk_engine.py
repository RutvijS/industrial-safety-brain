"""
risk_engine.py -- Hybrid Compound Risk Detection Engine.

Architecture:
    PlantStateService -> CompoundRiskEngine -> RiskAssessment -> Gemini (explanation only)

The engine is split into three modular components:
    RiskRuleEngine       - evaluates compound rules against a ZoneState
    RiskScoringEngine    - computes weighted risk scores from sensor + operational data
    RiskAssessmentBuilder - assembles the final assessment and optionally adds Gemini explanation

IMPORTANT: The engine is DETERMINISTIC. Given the same PlantState, it always
produces the same RiskAssessment. Gemini never influences the score.
"""

from datetime import datetime
from typing import Dict, List, Optional

from app.models.plant_state_models import ZoneState
from app.models.risk_models import (
    DetectedRisk,
    PlantRiskAssessment,
    Recommendation,
    RiskEvidence,
    RiskFactor,
    ZoneRiskAssessment,
)
from app.services.risk_config import (
    BASE_CONFIDENCE,
    COMPOUND_MULTIPLIER_MAX,
    COMPOUND_MULTIPLIER_MIN,
    COMPOUND_RULES,
    CONFIDENCE_PER_EVIDENCE,
    FACTOR_WEIGHTS,
    HAZARD_LEVELS,
    HIGH_RISK_PERMIT_TYPES,
    RISK_LEVELS,
    SENSOR_THRESHOLDS,
)


# ── Condition Evaluators ────────────────────────────────────
# Each maps a condition_key from risk_config to a function
# that takes a ZoneState and returns (bool, optional_evidence_detail).

def _check_high_gas(zone: ZoneState) -> tuple:
    avg = zone.current_sensor_status.avg_gas_level
    threshold = SENSOR_THRESHOLDS["gas_level"][0]
    return (avg >= threshold, f"Avg gas level: {avg} ppm (threshold: {threshold})")


def _check_high_temperature(zone: ZoneState) -> tuple:
    avg = zone.current_sensor_status.avg_temperature
    threshold = SENSOR_THRESHOLDS["temperature"][0]
    return (avg >= threshold, f"Avg temperature: {avg} C (threshold: {threshold})")


def _check_high_pressure(zone: ZoneState) -> tuple:
    avg = zone.current_sensor_status.avg_pressure
    threshold = SENSOR_THRESHOLDS["pressure"][0]
    return (avg >= threshold, f"Avg pressure: {avg} bar (threshold: {threshold})")


def _check_high_vibration(zone: ZoneState) -> tuple:
    avg = zone.current_sensor_status.avg_vibration
    threshold = SENSOR_THRESHOLDS["vibration"][0]
    return (avg >= threshold, f"Avg vibration: {avg} mm/s (threshold: {threshold})")


def _check_hot_work_active(zone: ZoneState) -> tuple:
    hot_work = [p for p in zone.active_permits if p.permit_type == "Hot Work"]
    return (len(hot_work) > 0, f"{len(hot_work)} active Hot Work permit(s)")


def _check_confined_space_active(zone: ZoneState) -> tuple:
    confined = [p for p in zone.active_permits if p.permit_type == "Confined Space Entry"]
    return (len(confined) > 0, f"{len(confined)} active Confined Space permit(s)")


def _check_valve_maintenance_active(zone: ZoneState) -> tuple:
    valve_maint = [
        m for m in zone.active_maintenance
        if "valve" in m.equipment.lower()
    ]
    return (len(valve_maint) > 0, f"{len(valve_maint)} valve maintenance job(s) active")


def _check_maintenance_active(zone: ZoneState) -> tuple:
    count = len(zone.active_maintenance)
    return (count > 0, f"{count} active maintenance job(s)")


def _check_night_shift(zone: ZoneState) -> tuple:
    if zone.current_shift and zone.current_shift.shift_name == "Night":
        return (True, f"Night shift active (supervisor: {zone.current_shift.supervisor})")
    return (False, "")


def _check_recent_similar_incident(zone: ZoneState) -> tuple:
    count = len(zone.recent_incidents)
    if count > 0:
        latest = zone.recent_incidents[0]
        return (True, f"{count} recent incident(s), latest: {latest.incident_id} - {latest.description[:60]}")
    return (False, "")


def _check_chemical_zone(zone: ZoneState) -> tuple:
    is_chemical = zone.zone == "Zone D" or "chemical" in zone.zone_name.lower()
    return (is_chemical, f"Zone type: {zone.zone_name} ({zone.risk_type})")


def _check_boiler_zone(zone: ZoneState) -> tuple:
    is_boiler = zone.zone == "Zone B" or "boiler" in zone.zone_name.lower()
    return (is_boiler, f"Zone type: {zone.zone_name} ({zone.risk_type})")


def _check_multiple_critical_sensors(zone: ZoneState) -> tuple:
    count = zone.current_sensor_status.critical_count
    return (count >= 2, f"{count} sensors in Critical state")


def _check_any_critical_sensor(zone: ZoneState) -> tuple:
    count = zone.current_sensor_status.critical_count
    return (count >= 1, f"{count} sensor(s) in Critical state")


def _check_high_worker_count(zone: ZoneState) -> tuple:
    count = zone.overall_context.worker_count
    return (count >= 4, f"{count} workers on shift")


def _check_high_risk_operations(zone: ZoneState) -> tuple:
    count = zone.overall_context.high_risk_operations
    return (count > 0, f"{count} high-risk operation(s) active")


def _check_overdue_maintenance(zone: ZoneState) -> tuple:
    overdue = [m for m in zone.active_maintenance if m.status == "Overdue"]
    return (len(overdue) > 0, f"{len(overdue)} overdue maintenance job(s)")


# Map condition_keys to evaluator functions
CONDITION_EVALUATORS: Dict[str, callable] = {
    "high_gas": _check_high_gas,
    "high_temperature": _check_high_temperature,
    "high_pressure": _check_high_pressure,
    "high_vibration": _check_high_vibration,
    "hot_work_active": _check_hot_work_active,
    "confined_space_active": _check_confined_space_active,
    "valve_maintenance_active": _check_valve_maintenance_active,
    "maintenance_active": _check_maintenance_active,
    "night_shift": _check_night_shift,
    "recent_similar_incident": _check_recent_similar_incident,
    "chemical_zone": _check_chemical_zone,
    "boiler_zone": _check_boiler_zone,
    "multiple_critical_sensors": _check_multiple_critical_sensors,
    "any_critical_sensor": _check_any_critical_sensor,
    "high_worker_count": _check_high_worker_count,
    "high_risk_operations": _check_high_risk_operations,
    "overdue_maintenance": _check_overdue_maintenance,
}


# ── RiskRuleEngine ──────────────────────────────────────────

class RiskRuleEngine:
    """Evaluates compound risk rules against a ZoneState.

    Each rule has multiple conditions. All conditions must be true
    for the compound risk to fire. Evidence is collected from each
    satisfied condition.
    """

    def evaluate(self, zone: ZoneState) -> List[DetectedRisk]:
        """Evaluate all compound rules and return detected risks."""
        detected: List[DetectedRisk] = []

        for rule in COMPOUND_RULES:
            all_met = True
            evidence_items: List[RiskEvidence] = []

            for cond_key in rule["condition_keys"]:
                evaluator = CONDITION_EVALUATORS.get(cond_key)
                if evaluator is None:
                    all_met = False
                    break

                is_met, detail = evaluator(zone)
                if not is_met:
                    all_met = False
                    break

                evidence_items.append(RiskEvidence(
                    source=cond_key,
                    detail=detail,
                    value=cond_key,
                ))

            if all_met:
                detected.append(DetectedRisk(
                    name=rule["name"],
                    severity=rule["severity"],
                    description=rule["description"],
                    evidence=evidence_items,
                    score_boost=rule["score_boost"],
                ))

        return detected


# ── RiskScoringEngine ───────────────────────────────────────

class RiskScoringEngine:
    """Computes weighted risk scores from sensor data and operational context.

    Score = sum(factor_score * factor_weight / 100) + compound_boost
    Final score is clamped to 0-100.
    """

    def _normalize_sensor_value(self, value: float, threshold_key: str) -> float:
        """Normalize a sensor value to 0-100 based on thresholds."""
        if threshold_key not in SENSOR_THRESHOLDS:
            return 0.0
        warn, crit = SENSOR_THRESHOLDS[threshold_key]
        if value <= 0:
            return 0.0
        if value >= crit:
            return 100.0
        if value >= warn:
            # Linear interpolation between warning (50) and critical (100)
            return 50.0 + 50.0 * (value - warn) / (crit - warn)
        # Below warning: linear 0-50
        return min(50.0, 50.0 * value / warn)

    def _score_gas(self, zone: ZoneState) -> RiskFactor:
        avg = zone.current_sensor_status.avg_gas_level
        norm = self._normalize_sensor_value(avg, "gas_level")
        weight = FACTOR_WEIGHTS["gas_level"]
        status = "Critical" if norm >= 75 else "Warning" if norm >= 50 else "Normal"
        return RiskFactor(
            name="gas_level", raw_value=avg, normalized_score=round(norm, 1),
            weight=weight, weighted_score=round(norm * weight / 100, 2), status=status,
        )

    def _score_temperature(self, zone: ZoneState) -> RiskFactor:
        avg = zone.current_sensor_status.avg_temperature
        norm = self._normalize_sensor_value(avg, "temperature")
        weight = FACTOR_WEIGHTS["temperature"]
        status = "Critical" if norm >= 75 else "Warning" if norm >= 50 else "Normal"
        return RiskFactor(
            name="temperature", raw_value=avg, normalized_score=round(norm, 1),
            weight=weight, weighted_score=round(norm * weight / 100, 2), status=status,
        )

    def _score_pressure(self, zone: ZoneState) -> RiskFactor:
        avg = zone.current_sensor_status.avg_pressure
        norm = self._normalize_sensor_value(avg, "pressure")
        weight = FACTOR_WEIGHTS["pressure"]
        status = "Critical" if norm >= 75 else "Warning" if norm >= 50 else "Normal"
        return RiskFactor(
            name="pressure", raw_value=avg, normalized_score=round(norm, 1),
            weight=weight, weighted_score=round(norm * weight / 100, 2), status=status,
        )

    def _score_permits(self, zone: ZoneState) -> RiskFactor:
        high_risk_count = sum(
            1 for p in zone.active_permits if p.permit_type in HIGH_RISK_PERMIT_TYPES
        )
        total_permits = len(zone.active_permits)
        # Score based on high-risk permit density
        norm = min(100.0, high_risk_count * 40.0 + total_permits * 10.0)
        weight = FACTOR_WEIGHTS["permit_risk"]
        status = "Critical" if norm >= 75 else "Warning" if norm >= 50 else "Normal"
        return RiskFactor(
            name="permit_risk", raw_value=float(high_risk_count), normalized_score=round(norm, 1),
            weight=weight, weighted_score=round(norm * weight / 100, 2), status=status,
        )

    def _score_maintenance(self, zone: ZoneState) -> RiskFactor:
        active = len(zone.active_maintenance)
        overdue = sum(1 for m in zone.active_maintenance if m.status == "Overdue")
        norm = min(100.0, overdue * 40.0 + active * 15.0)
        weight = FACTOR_WEIGHTS["maintenance_risk"]
        status = "Critical" if norm >= 75 else "Warning" if norm >= 50 else "Normal"
        return RiskFactor(
            name="maintenance_risk", raw_value=float(active), normalized_score=round(norm, 1),
            weight=weight, weighted_score=round(norm * weight / 100, 2), status=status,
        )

    def _score_shift(self, zone: ZoneState) -> RiskFactor:
        is_night = (
            zone.current_shift is not None
            and zone.current_shift.shift_name == "Night"
        )
        worker_count = zone.overall_context.worker_count
        # Night shift = higher risk, more workers = more exposure
        norm = 0.0
        if is_night:
            norm = 60.0 + min(40.0, worker_count * 8.0)
        else:
            norm = min(40.0, worker_count * 5.0)
        weight = FACTOR_WEIGHTS["shift_risk"]
        status = "Warning" if is_night else "Normal"
        return RiskFactor(
            name="shift_risk", raw_value=float(worker_count), normalized_score=round(norm, 1),
            weight=weight, weighted_score=round(norm * weight / 100, 2), status=status,
        )

    def _score_incidents(self, zone: ZoneState) -> RiskFactor:
        count = len(zone.recent_incidents)
        severe = sum(
            1 for i in zone.recent_incidents
            if i.severity in ("Critical", "Fatal", "Serious")
        )
        norm = min(100.0, severe * 30.0 + count * 10.0)
        weight = FACTOR_WEIGHTS["incident_history"]
        status = "Critical" if norm >= 75 else "Warning" if norm >= 50 else "Normal"
        return RiskFactor(
            name="incident_history", raw_value=float(count), normalized_score=round(norm, 1),
            weight=weight, weighted_score=round(norm * weight / 100, 2), status=status,
        )

    def compute(self, zone: ZoneState, detected_risks: List[DetectedRisk]) -> tuple:
        """Compute risk factors and total score.

        Returns:
            (risk_factors: List[RiskFactor], total_score: int)
        """
        factors = [
            self._score_gas(zone),
            self._score_temperature(zone),
            self._score_pressure(zone),
            self._score_permits(zone),
            self._score_maintenance(zone),
            self._score_shift(zone),
            self._score_incidents(zone),
        ]

        base_score = sum(f.weighted_score for f in factors)

        # Apply compound risk boost
        compound_boost = sum(r.score_boost for r in detected_risks)

        # Apply multiplier based on number of compound risks
        num_compounds = len(detected_risks)
        if num_compounds > 0:
            multiplier = min(
                COMPOUND_MULTIPLIER_MAX,
                COMPOUND_MULTIPLIER_MIN + 0.1 * num_compounds,
            )
        else:
            multiplier = 1.0

        total = base_score * multiplier + compound_boost
        total = max(0, min(100, int(round(total))))

        return factors, total


# ── RiskAssessmentBuilder ───────────────────────────────────

class RiskAssessmentBuilder:
    """Assembles the final RiskAssessment from rule + scoring outputs.

    Optionally sends the structured result to Gemini for explanation.
    Gemini NEVER influences the score.
    """

    def __init__(self) -> None:
        self._rule_engine = RiskRuleEngine()
        self._scoring_engine = RiskScoringEngine()

    @staticmethod
    def _get_risk_level(score: int) -> str:
        for threshold, level in RISK_LEVELS:
            if score >= threshold:
                return level
        return "LOW"

    @staticmethod
    def _get_hazard_level(score: int) -> str:
        for threshold, level in HAZARD_LEVELS:
            if score >= threshold:
                return level
        return "Very Low"

    @staticmethod
    def _compute_confidence(evidence: List[RiskEvidence], factors: List[RiskFactor]) -> int:
        confidence = BASE_CONFIDENCE
        confidence += len(evidence) * CONFIDENCE_PER_EVIDENCE
        # Boost confidence if many factors have data
        confidence += sum(1 for f in factors if f.raw_value > 0) * 2
        return min(99, confidence)

    @staticmethod
    def _build_reasoning(
        zone: ZoneState,
        factors: List[RiskFactor],
        detected: List[DetectedRisk],
    ) -> List[str]:
        """Build human-readable reasoning chain."""
        reasoning = []
        reasoning.append(f"Analyzed zone {zone.zone} ({zone.zone_name}) - {zone.risk_type}")

        warning_factors = [f for f in factors if f.status in ("Warning", "Critical")]
        if warning_factors:
            names = ", ".join(f.name for f in warning_factors)
            reasoning.append(f"Elevated risk factors detected: {names}")

        if detected:
            for d in detected:
                reasoning.append(f"Compound risk detected: {d.name} (severity: {d.severity})")

        if zone.current_shift:
            reasoning.append(
                f"Current shift: {zone.current_shift.shift_name} "
                f"with {zone.overall_context.worker_count} workers"
            )

        if zone.recent_incidents:
            reasoning.append(f"{len(zone.recent_incidents)} recent incident(s) in this zone")

        return reasoning

    @staticmethod
    def _build_recommendations(
        detected: List[DetectedRisk],
        factors: List[RiskFactor],
        risk_level: str,
    ) -> List[Recommendation]:
        """Generate actionable recommendations based on detected risks."""
        recs: List[Recommendation] = []

        # Recommendations from compound risks
        for d in detected:
            priority = "IMMEDIATE" if d.severity == "Critical" else "HIGH" if d.severity == "High" else "MEDIUM"
            recs.append(Recommendation(
                priority=priority,
                action=f"Address compound risk: {d.name}",
                reasoning=d.description,
            ))

        # Recommendations from elevated factors
        for f in factors:
            if f.status == "Critical":
                recs.append(Recommendation(
                    priority="IMMEDIATE",
                    action=f"Investigate critical {f.name} readings (value: {f.raw_value})",
                    reasoning=f"{f.name} is at critical levels requiring immediate attention.",
                ))
            elif f.status == "Warning":
                recs.append(Recommendation(
                    priority="HIGH",
                    action=f"Monitor elevated {f.name} (value: {f.raw_value})",
                    reasoning=f"{f.name} is at warning levels and trending toward critical.",
                ))

        # General recommendations based on overall risk
        if risk_level in ("CRITICAL", "HIGH"):
            recs.append(Recommendation(
                priority="HIGH",
                action="Review emergency response procedures for this zone",
                reasoning="Overall risk level warrants emergency preparedness review.",
            ))

        return recs

    @staticmethod
    def _collect_evidence(
        zone: ZoneState,
        factors: List[RiskFactor],
        detected: List[DetectedRisk],
    ) -> List[RiskEvidence]:
        """Collect all supporting evidence from factors and detected risks."""
        evidence: List[RiskEvidence] = []

        # Evidence from risk factors
        for f in factors:
            if f.status in ("Warning", "Critical"):
                evidence.append(RiskEvidence(
                    source=f"sensor/{f.name}",
                    detail=f"{f.name} = {f.raw_value} ({f.status})",
                    value=str(f.raw_value),
                ))

        # Evidence from compound risks
        for d in detected:
            for e in d.evidence:
                evidence.append(e)

        # Evidence from operational context
        if zone.active_permits:
            evidence.append(RiskEvidence(
                source="permits",
                detail=f"{len(zone.active_permits)} active permit(s)",
                value=", ".join(p.permit_id for p in zone.active_permits[:5]),
            ))

        if zone.active_maintenance:
            evidence.append(RiskEvidence(
                source="maintenance",
                detail=f"{len(zone.active_maintenance)} active maintenance job(s)",
                value=", ".join(m.maintenance_id for m in zone.active_maintenance[:5]),
            ))

        if zone.recent_incidents:
            evidence.append(RiskEvidence(
                source="incidents",
                detail=f"{len(zone.recent_incidents)} recent incident(s)",
                value=", ".join(i.incident_id for i in zone.recent_incidents[:5]),
            ))

        return evidence

    def analyze_zone(self, zone: ZoneState) -> ZoneRiskAssessment:
        """Run the full risk analysis pipeline for a single zone.

        1. Evaluate compound rules
        2. Compute weighted scores
        3. Build reasoning chain
        4. Generate recommendations
        5. Collect evidence
        """
        # Step 1: Detect compound risks
        detected = self._rule_engine.evaluate(zone)

        # Step 2: Compute scores
        factors, score = self._scoring_engine.compute(zone, detected)

        # Step 3: Derive levels
        risk_level = self._get_risk_level(score)
        hazard = self._get_hazard_level(score)

        # Step 4: Collect evidence
        evidence = self._collect_evidence(zone, factors, detected)

        # Step 5: Compute confidence
        confidence = self._compute_confidence(evidence, factors)

        # Step 6: Build reasoning
        reasoning = self._build_reasoning(zone, factors, detected)

        # Step 7: Generate recommendations
        recommendations = self._build_recommendations(detected, factors, risk_level)

        return ZoneRiskAssessment(
            zone=zone.zone,
            zone_name=zone.zone_name,
            overall_risk=risk_level,
            risk_score=score,
            confidence=confidence,
            hazard_level=hazard,
            risk_factors=factors,
            detected_compound_risks=detected,
            recommended_actions=recommendations,
            reasoning=reasoning,
            supporting_evidence=evidence,
            gemini_explanation=None,
            analyzed_at=datetime.utcnow().isoformat(),
        )

    # NOTE: analyze_zone_with_explanation() has been removed.
    # Gemini explanations are now handled by LLMSummaryService
    # which calls Gemini ONCE for the entire workflow.


# Singleton
risk_engine = RiskAssessmentBuilder()
