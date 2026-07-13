"""
prompt_builder.py -- Builds grounded prompts for Gemini from retrieved context.

Gemini must NEVER invent facts. It answers ONLY using retrieved context.
If evidence is missing, it must clearly state that.
"""

import os
from typing import List, Optional

from app.models.rag_models import RetrievedDocument
from app.models.risk_models import ZoneRiskAssessment

# Load prompt template
PROMPT_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "prompts", "incident_analysis_prompt.txt"
)


def _load_prompt_template() -> str:
    """Load the prompt template from disk."""
    if os.path.exists(PROMPT_TEMPLATE_PATH):
        with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()

    # Fallback inline template
    return """You are an industrial safety intelligence analyst.
Analyze the following risk assessment using ONLY the retrieved evidence below.

RISK ASSESSMENT:
{risk_context}

RETRIEVED EVIDENCE:
{evidence_context}

Provide your analysis in this format:

SUMMARY:
[2-3 sentence overview based on evidence]

WHY THIS IS DANGEROUS:
[Explain using retrieved evidence only]

HISTORICAL SIMILARITIES:
[List similar past incidents from the evidence]

LESSONS LEARNED:
[Key lessons from retrieved documents]

APPLICABLE REGULATIONS:
[Relevant regulations from retrieved documents]

RECOMMENDED ACTIONS:
1. [Action based on evidence]
2. [Action based on evidence]
3. [Action based on evidence]

CONFIDENCE: [HIGH/MEDIUM/LOW based on evidence quality]

IMPORTANT: Only reference information from the retrieved evidence.
If insufficient evidence exists, clearly state that."""


def build_risk_context(assessment: ZoneRiskAssessment) -> str:
    """Format risk assessment into context string."""
    lines = [
        f"Zone: {assessment.zone} ({assessment.zone_name})",
        f"Risk Level: {assessment.overall_risk}",
        f"Risk Score: {assessment.risk_score}/100",
        f"Hazard Level: {assessment.hazard_level}",
        f"Confidence: {assessment.confidence}%",
        "",
        "Detected Compound Risks:",
    ]

    if assessment.detected_compound_risks:
        for r in assessment.detected_compound_risks:
            lines.append(f"  - {r.name} (severity: {r.severity}): {r.description}")
    else:
        lines.append("  None detected")

    lines.append("")
    lines.append("Risk Factors:")
    for f in assessment.risk_factors:
        lines.append(f"  - {f.name}: {f.raw_value} (score: {f.normalized_score}/100, status: {f.status})")

    lines.append("")
    lines.append("Reasoning:")
    for r in assessment.reasoning:
        lines.append(f"  - {r}")

    return "\n".join(lines)


def build_evidence_context(documents: List[RetrievedDocument]) -> str:
    """Format retrieved documents into evidence context string."""
    if not documents:
        return "No relevant documents were retrieved. State this clearly in your analysis."

    lines = []
    for i, doc in enumerate(documents, 1):
        lines.append(f"[Document {i}]")
        lines.append(f"Source: {doc.source_filename}")
        lines.append(f"Type: {doc.document_type}")
        lines.append(f"Page: {doc.page_number}")
        lines.append(f"Section: {doc.section}")
        lines.append(f"Relevance: {doc.relevance_score:.2%}")
        lines.append(f"Content: {doc.content}")
        lines.append("")

    return "\n".join(lines)


def build_prompt(
    assessment: ZoneRiskAssessment,
    documents: List[RetrievedDocument],
) -> str:
    """Build the complete grounded prompt for Gemini.

    Args:
        assessment: The zone risk assessment to explain.
        documents: Retrieved evidence documents.

    Returns:
        Complete prompt string.
    """
    template = _load_prompt_template()
    risk_context = build_risk_context(assessment)
    evidence_context = build_evidence_context(documents)

    return template.format(
        risk_context=risk_context,
        evidence_context=evidence_context,
    )
