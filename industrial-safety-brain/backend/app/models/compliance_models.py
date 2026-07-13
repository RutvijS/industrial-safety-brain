"""
compliance_models.py -- Pydantic models for Compliance Intelligence,
Emergency Response, and Incident Report modules.

These models structure the output of the final functional layer.
They never calculate risk -- they consume existing assessments.
"""

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


# ── Compliance ──────────────────────────────────────────────

class RegulationFinding(BaseModel):
    """A single regulation finding."""

    regulation: str = Field(description="Regulation name/code")
    section: str = ""
    status: str = Field(description="Compliant, Non-Compliant, Warning")
    severity: str = Field(default="Medium", description="Critical, High, Medium, Low")
    description: str = ""
    evidence: str = ""
    source: str = ""


class CorrectiveAction(BaseModel):
    """A required corrective action."""

    priority: str = Field(description="Immediate, High, Medium, Low")
    action: str = ""
    regulation: str = ""
    deadline_hours: int = 24
    responsible: str = ""
    status: str = "Pending"


class ComplianceReport(BaseModel):
    """Complete compliance analysis output."""

    zone: str = ""
    zone_name: str = ""
    overall_status: str = Field(default="Compliant", description="Compliant, Non-Compliant, Warning")
    compliance_score: int = Field(default=100, description="0-100")
    risk_level: str = ""
    risk_score: int = 0
    total_findings: int = 0
    critical_findings: int = 0
    violated_regulations: List[RegulationFinding] = Field(default_factory=list)
    compliant_regulations: List[RegulationFinding] = Field(default_factory=list)
    corrective_actions: List[CorrectiveAction] = Field(default_factory=list)
    audit_summary: str = ""
    analyzed_at: str = ""


# ── Emergency Response ─────────────────────────────────────

class EmergencyAction(BaseModel):
    """A single emergency action step."""

    step: int = 0
    action: str = ""
    responsible: str = ""
    time_limit: str = ""
    category: str = ""


class EmergencyContact(BaseModel):
    """Emergency contact."""

    role: str = ""
    name: str = ""
    phone: str = ""
    priority: int = 1


class PPERequirement(BaseModel):
    """Required PPE item."""

    item: str = ""
    reason: str = ""
    mandatory: bool = True


class ChecklistItem(BaseModel):
    """A single checklist item."""

    item: str = ""
    status: str = "Pending"
    priority: str = "Medium"


class ResponseChecklist(BaseModel):
    """Categorized response checklist."""

    category: str = ""
    items: List[ChecklistItem] = Field(default_factory=list)


class EmergencyPlan(BaseModel):
    """Complete emergency response plan."""

    zone: str = ""
    zone_name: str = ""
    risk_level: str = ""
    risk_score: int = 0
    priority: str = ""
    incident_type: str = ""
    immediate_actions: List[EmergencyAction] = Field(default_factory=list)
    evacuation_plan: List[EmergencyAction] = Field(default_factory=list)
    isolation_procedure: List[EmergencyAction] = Field(default_factory=list)
    emergency_contacts: List[EmergencyContact] = Field(default_factory=list)
    required_ppe: List[PPERequirement] = Field(default_factory=list)
    medical_response: List[EmergencyAction] = Field(default_factory=list)
    recovery_checklist: List[ResponseChecklist] = Field(default_factory=list)
    incident_timeline: List[Dict[str, str]] = Field(default_factory=list)
    worker_count: int = 0
    generated_at: str = ""


# ── Incident Report ────────────────────────────────────────

class IncidentReport(BaseModel):
    """Auto-generated incident report (PDF-ready)."""

    report_id: str = ""
    timestamp: str = ""
    zone: str = ""
    zone_name: str = ""
    risk_level: str = ""
    risk_score: int = 0
    equipment_involved: List[str] = Field(default_factory=list)
    detected_risks: List[Dict[str, Any]] = Field(default_factory=list)
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, str]] = Field(default_factory=list)
    applicable_regulations: List[Dict[str, str]] = Field(default_factory=list)
    corrective_actions: List[Dict[str, str]] = Field(default_factory=list)
    emergency_priority: str = ""
    evacuation_required: bool = False
    worker_count: int = 0
    active_permits: int = 0
    executive_summary: str = ""
    export_format: str = "json"


# ── Request Models ──────────────────────────────────────────

class ZoneRequest(BaseModel):
    """Simple zone request for all three endpoints."""

    zone: str = Field(description="Zone to analyze (e.g. Zone A)")
