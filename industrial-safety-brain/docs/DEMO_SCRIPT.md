# Demo Script — Industrial Safety Brain
## 5–7 Minute Professional Demo

---

## Opening (30 seconds)

> "Good [morning/afternoon], we are **[Team Name]**.
>
> According to the International Labour Organization, over 2.3 million workers lose their lives each year due to work-related accidents and diseases. A major contributing factor? Safety systems that monitor sensors in isolation. A gas sensor flags independently. A temperature sensor flags separately. But the **combination** of elevated gas levels plus an active hot work permit — the kind of compound hazard that has contributed to several major industrial accidents — often goes undetected.
>
> We built **Industrial Safety Brain** — an AI-powered platform that detects compound industrial risks by analyzing multiple factors together, retrieves historical incident intelligence using RAG, and generates dynamic emergency response plans grounded in real data."

---

## Demo Flow

### Plant Overview (15 seconds)

> *Open the **Dashboard** landing page*

> "When you first open the platform, the Plant Overview dashboard gives you a summary of all zones, active alerts, and overall plant health at a glance. From here, you can navigate to any module."

---

### Step 1: Plant State (45 seconds)

> *Click the **Plant State** tab (🧠)*

> "This is our Unified Plant State Layer. It aggregates data from multiple sources — sensors, work permits, maintenance logs, shift rosters, and incident history — into a single consolidated view per zone.
>
> Zone A currently shows active sensors, work permits, and ongoing maintenance tasks. Notice how gas levels are elevated above the warning threshold.
>
> But that alone doesn't tell the full story. Let me show you what happens when we combine all the factors."

---

### Step 2: Risk Analysis (60 seconds)

> *Click the **Risk Analysis** tab (🔥), select Zone A*

> "Our Hybrid Compound Risk Detection Engine analyzes 7 weighted risk factors simultaneously — gas level, temperature, pressure, permit risk, maintenance risk, shift risk, and incident history. Each factor is normalized, weighted by domain importance, and scored deterministically.
>
> Here's the key: the engine detected a **compound risk** — elevated gas levels combined with an active hot work permit. This type of compound hazard has contributed to several major industrial accidents. No single sensor alarm would catch this — you need multi-factor analysis.
>
> **Importantly, risk scores are computed entirely by our deterministic rule engine. Gemini never calculates risk.** Gemini is only used once, at the end, to generate an evidence-backed executive summary explaining the findings in natural language.
>
> Below, you can see the recommended corrective actions with priority levels."

---

### Step 3: Incident Intelligence (45 seconds)

> *Click the **Incident Intel** tab (📚), query for Zone A*

> "This module uses Retrieval-Augmented Generation. We search our ChromaDB vector database for similar past incidents, lessons learned, and relevant regulations. The system retrieves matching documents with relevance scores.
>
> Every AI explanation is **grounded** — it only cites information from documents we actually retrieved. Every claim is backed by a citation. If no relevant evidence is found, the system states that explicitly rather than generating unsupported claims. For safety-critical decisions, this is non-negotiable."

---

### Step 4: Safety Heatmap (30 seconds)

> *Click the **Heatmap** tab (🗺️)*

> "The Geospatial Safety Heatmap gives plant managers a visual overview of the entire facility. Zones are color-coded by risk level — red zones need immediate attention, green zones are operating safely. Click any zone for drill-down details including worker count, permit status, and sensor readings.
>
> This provides a quick at-a-glance view of plant-wide safety status."

---

### Step 5: Knowledge Graph (30 seconds)

> *Click the **Knowledge Graph** tab (🕸️)*

> "Our Neo4j Knowledge Graph models the relationships between equipment, zones, workers, hazards, permits, regulations, and historical incidents. You can visually trace how a sensor connects to a piece of equipment, which links to a hazard, which maps to a specific regulation.
>
> This structural reasoning is what enables our Compliance module to cross-reference live sensor data against applicable regulations."

---

### Step 6: Multi-Agent Analysis (60 seconds)

> *Click the **Agent Analysis** tab (🤖), select Zone A, click Run*

> "This is the heart of the platform. Five specialized AI agents run in sequence — Risk, Incident Intelligence, Knowledge Graph, Compliance, and Emergency Response.
>
> Watch the pipeline execute..."
>
> *Wait for pipeline to complete*
>
> "Each agent performs a specialized task and passes structured data to the next. The Risk Agent's assessment becomes context for the Incident Agent, which becomes context for Compliance.
>
> If any agent fails — say Neo4j is down — the pipeline continues with partial results. This fault tolerance means you always get the best available analysis.
>
> At the bottom, the Response Aggregator produces a unified executive summary. This summary is generated by a **single Gemini API call** that combines all five agents' structured findings into a coherent explanation."

---

### Step 7: Compliance (45 seconds)

> *Click the **Compliance** tab (📋), run for Zone A*

> "The Compliance Intelligence module checks OISD, Factory Act, and DGMS regulations against live sensor data and risk assessment results.
>
> Each violation includes the regulatory reference, the evidence from sensor data, and a corrective action with priority level. The compliance score gives a snapshot of the zone's regulatory standing.
>
> This assists safety teams with continuous compliance monitoring — providing always-current regulatory visibility alongside the risk data."

---

### Step 8: Emergency Response (45 seconds)

> *Click the **Emergency** tab (🚨), generate for Zone A*

> "Based on the detected compound risk and current plant state, the system generates a **dynamic** emergency response plan — not a static template.
>
> It includes immediate actions with responsible persons and time limits, a numbered evacuation plan based on actual worker count, zone-specific PPE requirements, medical response steps, emergency contacts, and a recovery checklist.
>
> Notice the incident timeline — the plan adapts to the specific hazard detected. A gas-leak-during-hot-work scenario produces a different response than an equipment-failure scenario."

---

### Safety Chat (15 seconds)

> *Open the **Chat** panel*

> "The platform also includes a Safety Chat powered by Gemini. Safety officers can ask natural-language questions about hazards, PPE requirements, or OSHA regulations and get contextual responses. Responses are cached to minimize API usage."

---

### Step 9: Incident Report (30 seconds)

> *Click the **Report** tab (📄), generate for Zone A*

> "Finally, the platform auto-generates a structured incident report — with a unique report ID, timestamp, risk assessment data, applicable regulations, corrective actions, and an executive summary.
>
> This automates incident documentation and consolidates all supporting evidence into a single report, reducing the manual effort typically required to compile this information."

---

## Closing (30 seconds)

> "Industrial Safety Brain transforms fragmented sensor monitoring into unified, compound risk intelligence. It detects hazards no single sensor can identify, retrieves lessons from past incidents with full citations, maps regulatory compliance continuously, and generates dynamic emergency response plans grounded in real data.
>
> Every feature we demonstrated is implemented and running live. Our goal is to help safety teams act on intelligence, not just alarms.
>
> Thank you."

---

## Demo Tips

1. **Pre-load** all tabs before the demo to avoid cold-start delays
2. **Use Zone A** for the main demo — it has the most interesting compound risks
3. **Show Zone D** if a judge asks about low-risk scenarios (it shows Compliant/LOW)
4. **Keep Swagger open** in a background tab — judges may ask to see raw API responses
5. **Have the health endpoint ready** — `GET /health` shows all service connectivity
6. **Know the data source** — risk scores come from the deterministic engine, not Gemini
7. **If asked about Gemini**: "Gemini is called exactly once per workflow to generate the final summary. All risk scores, compliance findings, and emergency plans are computed deterministically."
