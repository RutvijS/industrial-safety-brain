"""
llm_summary_service.py -- Centralized LLM Aggregation Layer.

Architecture:
    Risk Engine (JSON)
    Incident Intelligence (JSON)
    Knowledge Graph (JSON)
    Compliance (JSON)
    Emergency Response (JSON)
        ↓
    LLMSummaryService  ──→  ONE Gemini Call
        ↓
    Unified Summary

IMPORTANT:
    - Every module passes ONLY structured data.
    - Gemini is invoked ONCE to produce a human-readable summary.
    - Gemini NEVER influences scores, risk levels, or compliance status.
    - Results are cached by content hash to avoid duplicate calls.

Future Compatibility:
    This service only calls `gemini_service.generate_response()`.
    To swap to Claude / GPT / Llama, replace GeminiService with any
    provider that exposes the same `generate_response(prompt) -> str` API.
"""

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("safety_brain.llm_summary")

# Cache TTL in seconds (5 minutes)
CACHE_TTL_SECONDS = 300

# Chat cache TTL (30 seconds — shorter to keep conversations responsive)
CHAT_CACHE_TTL_SECONDS = 30


# ── Prompt Templates ──────────────────────────────────────────

UNIFIED_SUMMARY_PROMPT = """You are SafetyBrain AI, a senior industrial safety analyst.
Analyze the following STRUCTURED DATA from multiple safety modules and produce a unified executive summary.

IMPORTANT RULES:
- Use ONLY the data provided below. Do NOT invent any values, sensor readings, or incidents.
- If a section has no data, say "No data available for this module."
- Be factual, concise, and actionable.

═══════════════════════════════════════════
RISK ASSESSMENT DATA
═══════════════════════════════════════════
{risk_data}

═══════════════════════════════════════════
INCIDENT INTELLIGENCE (RAG)
═══════════════════════════════════════════
{incident_data}

═══════════════════════════════════════════
KNOWLEDGE GRAPH INSIGHTS
═══════════════════════════════════════════
{knowledge_graph_data}

═══════════════════════════════════════════
COMPLIANCE FINDINGS
═══════════════════════════════════════════
{compliance_data}

═══════════════════════════════════════════
EMERGENCY RESPONSE PLAN
═══════════════════════════════════════════
{emergency_data}

═══════════════════════════════════════════

Provide your response in this EXACT format:

EXECUTIVE SUMMARY:
[3-4 sentence overview of the overall safety situation]

OVERALL RISK: [CRITICAL / HIGH / MEDIUM / LOW]

KEY FINDINGS:
1. [Most critical finding from the data]
2. [Second most critical finding]
3. [Third finding]

HISTORICAL SIMILARITIES:
[Any similar past incidents found in the incident intelligence data, or "None found" if no RAG data]

COMPLIANCE CONCERNS:
[Key regulatory issues from compliance data, or "All compliant" if no violations]

RECOMMENDED ACTIONS:
1. [Most urgent action with reasoning]
2. [Second priority action]
3. [Third priority action]

CONFIDENCE: [HIGH / MEDIUM / LOW based on data completeness]

Do NOT add any information beyond what is provided in the structured data above."""


CHAT_SYSTEM_CONTEXT = """You are SafetyBrain AI, an expert industrial safety assistant.
You provide accurate, concise guidance on workplace safety,
hazard identification, OSHA regulations, risk assessments,
PPE requirements, and incident prevention.
Always prioritize worker safety in your responses."""


# ── Cache ─────────────────────────────────────────────────────

class _SummaryCache:
    """Simple in-memory cache keyed by content hash with TTL."""

    def __init__(self, ttl: int = CACHE_TTL_SECONDS) -> None:
        self._store: Dict[str, tuple] = {}  # hash -> (response, timestamp)
        self._ttl = ttl

    def get(self, key: str) -> Optional[str]:
        """Return cached response if exists and not expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        response, ts = entry
        if time.time() - ts > self._ttl:
            del self._store[key]
            return None
        logger.info("LLM cache HIT for key=%s", key[:12])
        return response

    def put(self, key: str, response: str) -> None:
        """Store a response in the cache."""
        self._store[key] = (response, time.time())

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()


# ── Data Formatters ───────────────────────────────────────────
# These convert structured Pydantic/dict outputs into text blocks
# for the unified prompt. No Gemini calls happen here.

def _format_risk_data(risk_data: Optional[Dict[str, Any]]) -> str:
    """Format risk assessment data into a text block."""
    if not risk_data:
        return "No risk assessment data available."

    lines = []

    # Handle both single-zone and multi-zone formats
    zones = risk_data.get("zone_assessments", [])
    if zones:
        for z in zones:
            lines.append(f"\nZone: {z.get('zone', '?')} ({z.get('zone_name', '?')})")
            lines.append(f"  Risk Level: {z.get('overall_risk', 'N/A')}")
            lines.append(f"  Risk Score: {z.get('risk_score', 0)}/100")
            lines.append(f"  Hazard Level: {z.get('hazard_level', 'N/A')}")
            lines.append(f"  Confidence: {z.get('confidence', 0)}%")

            compounds = z.get("detected_compound_risks", [])
            if compounds:
                lines.append("  Compound Risks:")
                for r in compounds:
                    lines.append(f"    - {r.get('name', '?')} (severity: {r.get('severity', '?')}): {r.get('description', '')}")

            factors = z.get("risk_factors", [])
            elevated = [f for f in factors if f.get("status") in ("Warning", "Critical")]
            if elevated:
                lines.append("  Elevated Risk Factors:")
                for f in elevated:
                    lines.append(f"    - {f.get('name', '?')}: {f.get('raw_value', '?')} (status: {f.get('status', '?')})")

            recs = z.get("recommended_actions", [])
            if recs:
                lines.append("  Recommendations:")
                for r in recs[:3]:
                    lines.append(f"    - [{r.get('priority', '?')}] {r.get('action', '?')}")
    else:
        # Single zone format
        lines.append(f"Zone: {risk_data.get('zone', '?')} ({risk_data.get('zone_name', '?')})")
        lines.append(f"Risk Level: {risk_data.get('overall_risk', 'N/A')}")
        lines.append(f"Risk Score: {risk_data.get('risk_score', 0)}/100")
        lines.append(f"Hazard Level: {risk_data.get('hazard_level', 'N/A')}")

        compounds = risk_data.get("detected_compound_risks", [])
        if compounds:
            lines.append("Compound Risks:")
            for r in compounds:
                lines.append(f"  - {r.get('name', '?')} (severity: {r.get('severity', '?')}): {r.get('description', '')}")

        factors = risk_data.get("risk_factors", [])
        elevated = [f for f in factors if f.get("status") in ("Warning", "Critical")]
        if elevated:
            lines.append("Elevated Risk Factors:")
            for f in elevated:
                lines.append(f"  - {f.get('name', '?')}: {f.get('raw_value', '?')} (status: {f.get('status', '?')})")

    return "\n".join(lines) if lines else "No risk data."


def _format_incident_data(incident_data: Optional[Dict[str, Any]]) -> str:
    """Format incident intelligence (RAG) data into a text block."""
    if not incident_data:
        return "No incident intelligence data available."

    lines = []
    incidents = incident_data.get("similar_incidents", [])
    if incidents:
        lines.append(f"Similar Incidents Found: {len(incidents)}")
        for inc in incidents[:5]:
            lines.append(f"  - {inc.get('title', '?')} (type: {inc.get('document_type', '?')}, relevance: {inc.get('relevance', 0):.0%})")
            preview = inc.get("content_preview", "")
            if preview:
                lines.append(f"    Preview: {preview[:200]}")

    lessons = incident_data.get("lessons_learned", [])
    if lessons:
        lines.append(f"Lessons Learned: {len(lessons)}")
        for l in lessons[:3]:
            lines.append(f"  - {l.get('lesson', '?')[:200]} (source: {l.get('source', '?')})")

    regs = incident_data.get("related_regulations", [])
    if regs:
        lines.append(f"Related Regulations: {len(regs)}")
        for r in regs[:3]:
            lines.append(f"  - {r.get('title', '?')} ({r.get('document_type', '?')})")

    return "\n".join(lines) if lines else "No incident intelligence data."


def _format_knowledge_graph_data(kg_data: Optional[Dict[str, Any]]) -> str:
    """Format knowledge graph data into a text block."""
    if not kg_data:
        return "No knowledge graph data available."

    if not kg_data.get("available", False):
        return f"Knowledge graph not available: {kg_data.get('reason', 'unknown')}"

    lines = [
        f"Zone: {kg_data.get('zone', '?')} ({kg_data.get('zone_name', '?')})",
        f"Total Nodes: {kg_data.get('total_nodes', 0)}",
        f"Total Edges: {kg_data.get('total_edges', 0)}",
    ]

    node_types = kg_data.get("node_types", {})
    if node_types:
        lines.append("Node Types: " + ", ".join(f"{k}: {v}" for k, v in node_types.items()))

    hazards = kg_data.get("hazards", [])
    if hazards:
        lines.append("Hazards: " + ", ".join(h.get("name", "?") for h in hazards[:5]))

    regulations = kg_data.get("regulations", [])
    if regulations:
        lines.append("Regulations: " + ", ".join(r.get("name", "?") for r in regulations[:5]))

    equipment = kg_data.get("connected_equipment", [])
    if equipment:
        lines.append(f"Connected Equipment: {', '.join(equipment[:5])}")

    return "\n".join(lines)


def _format_compliance_data(compliance_data: Optional[Dict[str, Any]]) -> str:
    """Format compliance findings into a text block."""
    if not compliance_data:
        return "No compliance data available."

    lines = [
        f"Overall Status: {compliance_data.get('overall_status', 'N/A')}",
        f"Compliance Score: {compliance_data.get('compliance_score', 0)}/100",
        f"Total Findings: {compliance_data.get('total_findings', 0)}",
        f"Critical Findings: {compliance_data.get('critical_findings', 0)}",
    ]

    violated = compliance_data.get("violated_regulations", [])
    if violated:
        lines.append("Violations:")
        for v in violated[:5]:
            lines.append(f"  - {v.get('regulation', '?')} ({v.get('severity', '?')}): {v.get('description', '')}")

    actions = compliance_data.get("corrective_actions", [])
    if actions:
        lines.append("Corrective Actions:")
        for a in actions[:5]:
            lines.append(f"  - [{a.get('priority', '?')}] {a.get('action', '')} (regulation: {a.get('regulation', '?')})")

    return "\n".join(lines)


def _format_emergency_data(emergency_data: Optional[Dict[str, Any]]) -> str:
    """Format emergency response plan into a text block."""
    if not emergency_data:
        return "No emergency response data available."

    lines = [
        f"Priority: {emergency_data.get('priority', 'N/A')}",
        f"Incident Type: {emergency_data.get('incident_type', 'N/A')}",
        f"Worker Count: {emergency_data.get('worker_count', 0)}",
    ]

    immediate = emergency_data.get("immediate_actions", [])
    if immediate:
        lines.append(f"Immediate Actions: {len(immediate)}")
        for a in immediate[:3]:
            action_text = a.get("action", "") if isinstance(a, dict) else str(a)
            lines.append(f"  - {action_text}")

    evac = emergency_data.get("evacuation_plan", emergency_data.get("evacuation_steps", []))
    if evac:
        lines.append(f"Evacuation Steps: {len(evac)}")

    ppe = emergency_data.get("required_ppe", [])
    if ppe:
        mandatory = [p for p in ppe if (p.get("mandatory", False) if isinstance(p, dict) else False)]
        lines.append(f"Mandatory PPE: {len(mandatory)} items")

    return "\n".join(lines)


# ── Content Hash ──────────────────────────────────────────────

def _compute_hash(*parts: Any) -> str:
    """Compute a SHA-256 hash of all parts for cache keying."""
    h = hashlib.sha256()
    for part in parts:
        if part is None:
            h.update(b"null")
        elif isinstance(part, (dict, list)):
            h.update(json.dumps(part, sort_keys=True, default=str).encode())
        else:
            h.update(str(part).encode())
    return h.hexdigest()


# ── LLM Summary Service ──────────────────────────────────────

class LLMSummaryService:
    """Centralized service for all LLM summarization.

    Receives structured data from all modules, constructs ONE prompt,
    calls Gemini ONCE, and returns the unified summary.

    All caching is handled internally via content hashing.
    """

    def __init__(self) -> None:
        self._cache = _SummaryCache(ttl=CACHE_TTL_SECONDS)
        self._chat_cache = _SummaryCache(ttl=CHAT_CACHE_TTL_SECONDS)

    async def summarize(
        self,
        risk_data: Optional[Dict[str, Any]] = None,
        incident_data: Optional[Dict[str, Any]] = None,
        knowledge_graph_data: Optional[Dict[str, Any]] = None,
        compliance_data: Optional[Dict[str, Any]] = None,
        emergency_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a unified summary from all module outputs.

        This is the ONLY place where Gemini is called for analysis workflows.
        ONE call per invocation (or zero if cached).

        Args:
            risk_data: Structured output from Risk Engine.
            incident_data: Structured output from Incident Intelligence (RAG).
            knowledge_graph_data: Structured output from Knowledge Graph.
            compliance_data: Structured output from Compliance Service.
            emergency_data: Structured output from Emergency Service.

        Returns:
            Unified executive summary string from Gemini.
        """
        # Check cache first
        cache_key = _compute_hash(
            risk_data, incident_data, knowledge_graph_data,
            compliance_data, emergency_data,
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        # Format all sections
        prompt = UNIFIED_SUMMARY_PROMPT.format(
            risk_data=_format_risk_data(risk_data),
            incident_data=_format_incident_data(incident_data),
            knowledge_graph_data=_format_knowledge_graph_data(knowledge_graph_data),
            compliance_data=_format_compliance_data(compliance_data),
            emergency_data=_format_emergency_data(emergency_data),
        )

        # ONE Gemini call
        logger.info("LLM Summary Service: calling Gemini (1 call)")
        try:
            from app.services.gemini_service import gemini_service
            response = await gemini_service.generate_response(prompt, caller="summarize")
        except Exception as e:
            logger.error("LLM Summary Service: Gemini call failed: %s", e)
            return self._fallback_summary(
                risk_data, incident_data, knowledge_graph_data,
                compliance_data, emergency_data,
            )

        # Cache the result
        self._cache.put(cache_key, response)
        return response

    async def summarize_agent_results(
        self,
        agent_results: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Generate a summary from agent pipeline results.

        Extracts structured data from each agent's output and delegates
        to the unified summarize() method.

        Args:
            agent_results: List of agent output dicts from format_output().

        Returns:
            Unified summary string, or None on failure.
        """
        risk_data = None
        incident_data = None
        kg_data = None
        compliance_data = None
        emergency_data = None

        for r in agent_results:
            if r.get("status") != "completed":
                continue
            name = r.get("agent_name", "")
            data = r.get("data", {})

            if name == "risk_agent":
                risk_data = data
            elif name == "incident_agent":
                incident_data = data
            elif name == "knowledge_graph_agent":
                kg_data = data
            elif name == "compliance_agent":
                compliance_data = data
            elif name == "emergency_response_agent":
                emergency_data = data

        return await self.summarize(
            risk_data=risk_data,
            incident_data=incident_data,
            knowledge_graph_data=kg_data,
            compliance_data=compliance_data,
            emergency_data=emergency_data,
        )

    async def chat(self, message: str) -> str:
        """Process a chat message through the LLM.

        Includes short-lived caching (30s) to prevent duplicate calls
        when the same message is sent rapidly.

        Args:
            message: User's chat message.

        Returns:
            AI response string.
        """
        # Check chat cache to avoid duplicate calls for identical messages
        cache_key = _compute_hash(message)
        cached = self._chat_cache.get(cache_key)
        if cached is not None:
            return cached

        from app.services.gemini_service import gemini_service
        response = await gemini_service.generate_response(message, caller="chat")

        # Cache with short TTL
        self._chat_cache.put(cache_key, response)
        return response

    @staticmethod
    def _fallback_summary(
        risk_data: Optional[Dict],
        incident_data: Optional[Dict],
        knowledge_graph_data: Optional[Dict],
        compliance_data: Optional[Dict],
        emergency_data: Optional[Dict],
    ) -> str:
        """Generate a deterministic fallback when Gemini is unavailable."""
        parts = ["Safety analysis summary (LLM unavailable):"]

        if risk_data:
            zones = risk_data.get("zone_assessments", [])
            if zones:
                worst = max(zones, key=lambda z: z.get("risk_score", 0))
                parts.append(
                    f"Highest risk: {worst.get('zone', '?')} "
                    f"({worst.get('overall_risk', '?')}, score: {worst.get('risk_score', 0)}/100)."
                )
            else:
                parts.append(
                    f"Risk: {risk_data.get('overall_risk', 'N/A')} "
                    f"(score: {risk_data.get('risk_score', 0)}/100)."
                )

        if compliance_data:
            parts.append(
                f"Compliance: {compliance_data.get('overall_status', 'N/A')} "
                f"({compliance_data.get('total_findings', 0)} findings)."
            )

        if emergency_data:
            parts.append(f"Emergency priority: {emergency_data.get('priority', 'N/A')}.")

        return " ".join(parts)

    def clear_cache(self) -> None:
        """Clear the summary and chat caches."""
        self._cache.clear()
        self._chat_cache.clear()
        logger.info("LLM Summary and chat caches cleared.")


# Singleton
llm_summary_service = LLMSummaryService()
