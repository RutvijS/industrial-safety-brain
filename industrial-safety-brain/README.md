# 🛡️ Industrial Safety Brain

### AI-Powered Industrial Safety Intelligence Platform

> A comprehensive, multi-agent AI platform that detects compound industrial risks in real-time, retrieves historical incident intelligence, maps regulatory compliance gaps, and orchestrates emergency response — all from a single unified dashboard.

---

## 🎯 Problem Statement

Industrial accidents kill **2.3 million workers globally every year** (ILO). In India alone, **over 1,100 major industrial accidents** were reported in a single year (DGFASLI). The root cause? **Fragmented safety systems** that monitor individual parameters in isolation.

**Current industry pain points:**
- Sensors monitor gas, temperature, pressure **independently** — no compound risk detection
- Incident learnings are buried in PDF reports nobody reads
- Regulatory compliance is checked manually once a year
- Emergency response plans are static documents, not dynamic systems
- No single platform connects risk → incidents → regulations → response

---

## 💡 Solution

**Industrial Safety Brain** is an AI-powered platform that:

1. **Detects compound risks** — identifies dangerous *combinations* of events (e.g., high gas + active hot work permit + expired maintenance = explosion risk)
2. **Retrieves incident intelligence** — uses RAG to surface similar past incidents, near-misses, and lessons learned
3. **Maps knowledge relationships** — builds a graph of equipment → zones → workers → hazards → regulations
4. **Orchestrates AI agents** — 5 specialized agents analyze risk, incidents, compliance, and emergency response in sequence
5. **Generates compliance reports** — automatically identifies regulatory violations with corrective actions
6. **Creates emergency plans** — dynamic evacuation, PPE, medical, and isolation procedures based on live risk data

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **Unified Plant State** | Real-time aggregation of sensors, permits, maintenance, shifts, and incidents per zone |
| 🔥 **Compound Risk Engine** | Detects 10+ compound risk patterns (gas + heat, pressure + vibration, etc.) with weighted scoring |
| 📚 **Incident Intelligence (RAG)** | Semantic search over industrial documents, SOPs, and regulations using ChromaDB + Gemini |
| 🗺️ **Safety Heatmap** | Interactive zone-by-zone risk visualization with drill-down details |
| 🕸️ **Knowledge Graph** | Neo4j-powered graph with 11 node types and 12 relationship types |
| 🤖 **Multi-Agent Orchestrator** | 5 specialized agents (Risk, Incident, KG, Compliance, Emergency) with fault tolerance |
| 📋 **Compliance Intelligence** | Automated OISD, Factory Act, DGMS regulation checking with gap analysis |
| 🚨 **Emergency Response** | Dynamic evacuation plans, PPE requirements, medical response, recovery checklists |
| 📄 **Incident Reports** | Auto-generated, PDF-ready incident reports with evidence and executive summary |
| 💬 **AI Safety Chat** | Natural language interface powered by Gemini for safety queries |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                   │
│  11 Pages: Chat │ Overview │ State │ Risk │ Intel │ Heatmap │
│  KnowledgeGraph │ Agents │ Compliance │ Emergency │ Report  │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API (Axios)
┌─────────────────────────▼───────────────────────────────────┐
│                   BACKEND (FastAPI)                           │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │Plant State│  │   Risk   │  │Incident  │  │ Geospatial │  │
│  │  Layer    │  │  Engine  │  │Intel(RAG)│  │  Service   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────────┘  │
│       │              │              │                         │
│  ┌────▼──────────────▼──────────────▼────────────────────┐  │
│  │           MULTI-AGENT ORCHESTRATOR                     │  │
│  │  ┌─────┐ ┌──────┐ ┌────┐ ┌──────────┐ ┌───────────┐  │  │
│  │  │Risk │ │Incid.│ │ KG │ │Compliance│ │Emergency  │  │  │
│  │  │Agent│→│Agent │→│Agt │→│  Agent   │→│Resp Agent │  │  │
│  │  └─────┘ └──────┘ └────┘ └──────────┘ └───────────┘  │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │                                   │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │              RESPONSE AGGREGATOR + GEMINI              │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                    │              │              │
          ┌────────▼──┐   ┌──────▼─────┐  ┌────▼────┐
          │  ChromaDB  │   │   Neo4j    │  │ Gemini  │
          │(Vector DB) │   │(Graph DB)  │  │  (LLM)  │
          └────────────┘   └────────────┘  └─────────┘
```

---

## 🔧 Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, Vanilla CSS |
| **Backend** | Python 3.10+, FastAPI, Pydantic |
| **AI/LLM** | Google Gemini 2.0 Flash |
| **Vector DB** | ChromaDB (in-process) |
| **Graph DB** | Neo4j (bolt protocol) |
| **Datasets** | Synthetic JSON (5 datasets, 4 zones) |

---

## 📁 Folder Structure

```
industrial-safety-brain/
├── backend/
│   ├── app/
│   │   ├── agents/          # 5 AI agents + orchestrator
│   │   ├── models/          # 10 Pydantic schema files
│   │   ├── routes/          # 10 API routers (25+ endpoints)
│   │   ├── rag/             # Document loader, vector store, retriever
│   │   └── services/        # 14 business logic services
│   └── requirements.txt
├── datasets/                # 5 synthetic industrial datasets
├── frontend/
│   └── src/
│       ├── pages/           # 11 page components
│       ├── components/      # Reusable UI components
│       └── services/        # API client
└── README.md
```

---

## 🚀 Installation & Running

### Backend
```bash
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
# Create .env with: GEMINI_API_KEY=your_key
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install && npm run dev
```

### Optional: Neo4j
```bash
# Install Neo4j Desktop or Docker
# Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in backend/.env
```

---

## 📸 Screenshots

> *Screenshots of each module to be added from live demo*

| Module | Screenshot |
|--------|-----------|
| Plant State Dashboard | *[screenshot]* |
| Risk Analysis | *[screenshot]* |
| Safety Heatmap | *[screenshot]* |
| Multi-Agent Analysis | *[screenshot]* |
| Compliance Report | *[screenshot]* |
| Emergency Response Plan | *[screenshot]* |

---

## 🔮 Future Improvements

- **Real-time sensor integration** via MQTT/OPC-UA
- **Mobile app** for field workers
- **Predictive maintenance** using ML on sensor trends
- **Automated regulatory reporting** to PESO/DGFASLI
- **Multi-plant support** with role-based access
- **Digital twin** integration for 3D visualization
- **Voice alerts** for critical compound risks

---

## 👥 Team

| Name | Role |
|------|------|
| *[Team Member 1]* | *[Role]* |
| *[Team Member 2]* | *[Role]* |

---

*Built for the ET Hackathon 2026*
