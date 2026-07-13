# Architecture — Industrial Safety Brain

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     FRONTEND (React 18 + Vite)                    │
│                                                                   │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │  Safety  │ │  Plant   │ │  Plant   │ │   Risk   │ │Incident│ │
│  │  Chat    │ │ Overview │ │  State   │ │ Analysis │ │  Intel │ │
│  └─────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ Heatmap │ │Knowledge │ │  Agent   │ │Compliance│ │Emergenc│ │
│  │         │ │  Graph   │ │ Analysis │ │          │ │y + Rpt │ │
│  └─────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │
│                          Axios API Client                         │
└──────────────────────────────┬────────────────────────────────────┘
                               │ HTTP/REST
┌──────────────────────────────▼────────────────────────────────────┐
│                      BACKEND (FastAPI)                             │
│                                                                    │
│  ┌────────────────── ROUTES (10 Routers) ─────────────────────┐   │
│  │ /chat │ /sensors │ /plant-state │ /risk-assessment │ /rag  │   │
│  │ /heatmap │ /knowledge-graph │ /agent-analysis              │   │
│  │ /compliance-analysis │ /emergency-response │ /reports      │   │
│  └───────────────────────────┬────────────────────────────────┘   │
│                              │                                     │
│  ┌───────────────── SERVICES (14 Modules) ────────────────────┐   │
│  │                                                             │   │
│  │  ┌──────────────┐    ┌─────────────────┐    ┌───────────┐ │   │
│  │  │  Plant State  │    │   Risk Engine    │    │Geospatial │ │   │
│  │  │   Service     │───▶│  (Compound Risk  │    │ Service   │ │   │
│  │  │  (Aggregator) │    │   Detection)     │    │ (Heatmap) │ │   │
│  │  └──────┬───────┘    └────────┬─────────┘    └───────────┘ │   │
│  │         │                     │                              │   │
│  │  ┌──────▼───────┐    ┌───────▼──────────┐                  │   │
│  │  │ Data Service  │    │  Incident Intel  │                  │   │
│  │  │ (JSON Loader) │    │  (RAG Pipeline)  │                  │   │
│  │  └──────────────┘    └──────────────────┘                  │   │
│  │                                                             │   │
│  │  ┌──────────────┐    ┌──────────────────┐                  │   │
│  │  │  Compliance   │    │   Emergency      │                  │   │
│  │  │  Service      │    │   Service        │                  │   │
│  │  └──────────────┘    └──────────────────┘                  │   │
│  │                                                             │   │
│  │  ┌──────────────┐    ┌──────────────────┐                  │   │
│  │  │Incident Rpt  │    │  Gemini Service  │                  │   │
│  │  │  Service      │    │  (LLM Wrapper)  │                  │   │
│  │  └──────────────┘    └──────────────────┘                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌───────────── AGENT ORCHESTRATOR ───────────────────────────┐   │
│  │                                                             │   │
│  │  Context ──▶ Risk ──▶ Incident ──▶ KG ──▶ Compliance ──▶  │   │
│  │              Agent    Agent       Agent    Agent            │   │
│  │                                              │              │   │
│  │              ◀──── Response Aggregator ◀─── Emergency ◀──  │   │
│  │                        + Gemini Summary      Agent          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌───────────── RAG PIPELINE ─────────────────────────────────┐   │
│  │  Document Loader ──▶ Vector Store ──▶ Retriever ──▶ Prompt │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────▼─────┐      ┌──────▼──────┐      ┌─────▼──────┐
    │ ChromaDB │      │   Neo4j     │      │  Gemini    │
    │Vector DB │      │  Graph DB   │      │  2.0 Flash │
    │(In-proc) │      │ (Optional)  │      │  (Google)  │
    └──────────┘      └─────────────┘      └────────────┘
```

## Data Flow

```
Synthetic Datasets (JSON)
    │
    ├── sensors.json       (100 readings, 4 zones)
    ├── permits.json       (20 work permits)
    ├── maintenance.json   (15 maintenance tasks)
    ├── shifts.json        (12 shift records)
    └── incidents.json     (10 historical incidents)
         │
         ▼
    Plant State Service ────────────────────────▶ Frontend
    (Aggregates per zone)                         (Plant State Page)
         │
         ▼
    Risk Engine ────────────────────────────────▶ Frontend
    (7 factors × weights × compound patterns)     (Risk Analysis)
         │
         ▼
    Agent Orchestrator
    ├── Risk Agent ──────────────────────────────┐
    ├── Incident Agent (RAG) ────────────────────┤
    ├── Knowledge Graph Agent ───────────────────┤──▶ Frontend
    ├── Compliance Agent ────────────────────────┤   (Agent Analysis)
    └── Emergency Agent ─────────────────────────┘
         │
         ▼
    Response Aggregator + Gemini Summary
         │
         ├── Compliance Report ──────────────────▶ Frontend (Compliance)
         ├── Emergency Plan ─────────────────────▶ Frontend (Emergency)
         └── Incident Report ────────────────────▶ Frontend (Report)
```

## Module Dependency Graph

```
                    Gemini Service
                    /     |     \
                   /      |      \
         Chat   RAG    Agents   Compliance
          |      |       |         |
          |      |       |    Risk Engine
          |      |       |    /    |
          |      |       |   /     |
          |    ChromaDB  | /  Plant State
          |              |/        |
          |         Neo4j      Data Service
          |                        |
          └────────────────── Datasets (JSON)
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Agents are wrappers, not implementations | Prevents logic duplication; Risk Engine stays the single source of truth |
| Sequential agent pipeline, not parallel | Each agent needs the previous agent's output as context |
| ChromaDB in-process | Zero deployment overhead; swap to Pinecone in production |
| Neo4j optional | Platform works without it; graph features degrade gracefully |
| Gemini summary optional | Core analysis works without LLM; summary is enhancement only |
| JSON datasets, not database | Hackathon speed; easily replaced with MQTT/OPC-UA/SQL |
| Vanilla CSS, not Tailwind | Full design control; consistent dark theme across 11 pages |
