# Demo Script — Industrial Safety Brain
## 5–7 Minute Professional Demo

---

## Opening (30 seconds)

> "Good [morning/afternoon], we are **[Team Name]**.
>
> Every year, 2.3 million workers die from industrial accidents. The number one reason? Safety systems that monitor sensors in isolation. A gas sensor flags independently. A temperature sensor flags separately. But the **combination** of high gas plus an active hot work permit — the combination that causes explosions — goes completely undetected.
>
> We built **Industrial Safety Brain** — an AI platform that detects compound industrial risks in real-time, retrieves historical incident intelligence, and orchestrates dynamic emergency response."

---

## Demo Flow

### Step 1: Plant State (45 seconds)

> *Click the **Plant State** tab (🧠)*

> "This is our Unified Plant State Layer. It aggregates data from 5 sources — sensors, work permits, maintenance logs, shift rosters, and incident history — into a single real-time view per zone.
>
> Zone A currently has 15 active sensors, 3 work permits, and 2 ongoing maintenance tasks. Notice how gas levels are elevated at 65 ppm — above the 50 ppm critical threshold.
>
> But that alone doesn't tell the full story. Let me show you what happens when we combine all the factors."

---

### Step 2: Risk Analysis (60 seconds)

> *Click the **Risk Analysis** tab (🔥), select Zone A*

> "Our Hybrid Compound Risk Engine analyzes 7 risk factors simultaneously — gas, temperature, pressure, vibration, humidity, active permits, and maintenance tasks. Each factor is normalized, weighted by domain importance, and scored.
>
> Zone A scores **73 out of 100** — HIGH risk. But here's the key insight: the engine detected a **compound risk**. Elevated gas levels combined with an active hot work permit. This is the exact combination that caused the Bhopal disaster. No single sensor alarm would catch this — you need multi-factor analysis.
>
> Below, you can see the recommended corrective actions with priority levels."

---

### Step 3: Incident Intelligence (45 seconds)

> *Click the **Incident Intel** tab (📚), query for Zone A*

> "Using Retrieval-Augmented Generation, we search our document index for similar past incidents. The system retrieved 2 similar incidents with lessons learned.
>
> Critically, our LLM is **grounded** — it only cites information from documents we actually retrieved. Every claim has a citation. No hallucination. For safety-critical decisions, this is non-negotiable."

---

### Step 4: Safety Heatmap (30 seconds)

> *Click the **Heatmap** tab (🗺️)*

> "The Geospatial Safety Heatmap gives plant managers an instant visual overview. Red zones need immediate attention. Green zones are safe. Click any zone for drill-down details — worker count, permit status, sensor readings.
>
> This replaces a safety officer walking the entire plant."

---

### Step 5: Knowledge Graph (30 seconds)

> *Click the **Knowledge Graph** tab (🕸️)*

> "Our Neo4j Knowledge Graph models relationships between equipment, zones, workers, hazards, and regulations. This zone has 47 connected entities. You can visually trace how a sensor relates to a piece of equipment, which relates to a hazard, which relates to a regulation.
>
> This structural reasoning is what enables the Compliance module."

---

### Step 6: Multi-Agent Analysis (60 seconds)

> *Click the **Agent Analysis** tab (🤖), select Zone A, click Run*

> "This is the heart of the platform. Five specialized AI agents run in sequence — Risk, Incident Intelligence, Knowledge Graph, Compliance, and Emergency Response.
>
> Watch the pipeline execute..."
>
> *Wait for pipeline to complete*
>
> "All 5 agents completed in under 2 seconds. Each agent's output feeds the next — the Risk Agent's assessment becomes context for the Incident Agent, which becomes context for Compliance.
>
> If any agent fails — say Neo4j is down — the pipeline continues. Partial results are still valuable. This fault tolerance is critical for production systems.
>
> At the bottom, the Response Aggregator produces a Gemini-powered executive summary combining all 5 agents' findings."

---

### Step 7: Compliance (45 seconds)

> *Click the **Compliance** tab (📋), run for Zone A*

> "The Compliance Intelligence module automatically checks OISD, Factory Act, and DGMS regulations against live sensor data.
>
> Zone A has a compliance score of **62 out of 100**. Three regulations are violated — including OISD-GDN-116 for gas detection. Each violation includes the evidence, the regulation text, and a corrective action with a deadline and responsible person.
>
> This replaces the annual compliance audit with continuous, real-time monitoring."

---

### Step 8: Emergency Response (45 seconds)

> *Click the **Emergency** tab (🚨), generate for Zone A*

> "Based on the detected compound risk — gas leak during hot work — the system generates a **dynamic** emergency plan. Not a generic template.
>
> It includes: 6 immediate actions with responsible persons and time limits, a numbered evacuation plan for 8 workers, zone-specific PPE requirements including SCBA, medical response steps, 8 emergency contacts, and a complete recovery checklist.
>
> Notice the incident timeline — from detection at T+0 to regulatory notification at T+60 minutes. This is a living document that adapts to the specific hazard detected."

---

### Step 9: Incident Report (30 seconds)

> *Click the **Report** tab (📄), generate for Zone A*

> "Finally, the platform auto-generates a complete incident report — with report ID, timestamp, all evidence, applicable regulations, corrective actions, and an executive summary. Click Print for a PDF-ready version.
>
> This report would normally take a safety officer 4-6 hours. We generate it in 2 seconds."

---

## Closing (30 seconds)

> "Industrial Safety Brain transforms reactive safety into proactive intelligence. It detects compound risks no single sensor can identify, retrieves lessons from past incidents, maps regulatory compliance in real-time, and orchestrates dynamic emergency response.
>
> Every year, 2.3 million workers don't come home. Our platform is built to change that.
>
> Thank you."

---

## Demo Tips

1. **Pre-load** all tabs before the demo to avoid cold-start delays
2. **Use Zone A** for the main demo — it has the most interesting compound risks
3. **Show Zone D** if a judge asks about low-risk scenarios (it shows Compliant/LOW)
4. **Keep Swagger open** in a background tab — judges may ask to see raw API responses
5. **Have the health endpoint ready** — `GET /health` shows all service connectivity
