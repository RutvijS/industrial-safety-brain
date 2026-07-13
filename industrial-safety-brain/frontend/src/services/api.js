import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Send a chat message to the backend and return the AI response.
 * @param {string} message - The user's message.
 * @returns {Promise<string>} The AI response text.
 */
export const sendMessage = async (message) => {
  const { data } = await api.post("/chat", { message });
  return data.response;
};

// ── Plant Data API ────────────────────────────────────────

/** Fetch all sensor readings, with optional query filters. */
export const getSensors = async (params = {}) => {
  const { data } = await api.get("/sensors", { params });
  return data;
};

/** Fetch all work permits, with optional query filters. */
export const getPermits = async (params = {}) => {
  const { data } = await api.get("/permits", { params });
  return data;
};

/** Fetch all maintenance records, with optional query filters. */
export const getMaintenance = async (params = {}) => {
  const { data } = await api.get("/maintenance", { params });
  return data;
};

/** Fetch all shift schedules, with optional query filters. */
export const getShifts = async (params = {}) => {
  const { data } = await api.get("/shifts", { params });
  return data;
};

/** Fetch all historical incidents, with optional query filters. */
export const getIncidents = async (params = {}) => {
  const { data } = await api.get("/incidents", { params });
  return data;
};

// ── Plant State API ───────────────────────────────────────

/** Fetch unified plant state for all zones. */
export const getPlantState = async () => {
  const { data } = await api.get("/plant-state");
  return data;
};

/** Fetch unified state for a single zone. */
export const getZoneState = async (zone) => {
  const { data } = await api.get(`/plant-state/${encodeURIComponent(zone)}`);
  return data;
};

/** Fetch high-level plant overview summary. */
export const getPlantOverviewSummary = async () => {
  const { data } = await api.get("/plant-overview");
  return data;
};

// ── Risk Analysis API ─────────────────────────────────────

/** Run full plant risk analysis (all zones). */
export const runRiskAnalysis = async () => {
  const { data } = await api.post("/risk-analysis");
  return data;
};

/** Run risk analysis for a single zone. */
export const getZoneRiskAnalysis = async (zone) => {
  const { data } = await api.get(`/risk-analysis/${encodeURIComponent(zone)}`);
  return data;
};

// ── Incident Intelligence API ─────────────────────────────

/** Run incident intelligence analysis for a zone. */
export const runIncidentIntelligence = async (zone, includeExplanation = true) => {
  const { data } = await api.post("/incident-intelligence", {
    zone,
    include_explanation: includeExplanation,
  });
  return data;
};

/** Upload and ingest documents into the vector store. */
export const ingestDocuments = async (files, documentType = "General") => {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  formData.append("document_type", documentType);
  const { data } = await api.post("/ingest-documents", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

/** List all indexed documents. */
export const getDocuments = async () => {
  const { data } = await api.get("/documents");
  return data;
};

// ── Geospatial Intelligence API ───────────────────────────

/** Fetch static plant layout. */
export const getPlantLayout = async () => {
  const { data } = await api.get("/plant-layout");
  return data;
};

/** Fetch live heatmap data for all zones. */
export const getHeatmapData = async () => {
  const { data } = await api.get("/heatmap");
  return data;
};

/** Fetch comprehensive details for a single zone. */
export const getZoneDetails = async (zone) => {
  const { data } = await api.get(`/zone-details/${encodeURIComponent(zone)}`);
  return data;
};

// ── Knowledge Graph API ───────────────────────────────────

/** Build the knowledge graph from datasets. */
export const buildKnowledgeGraph = async () => {
  const { data } = await api.post("/knowledge-graph/build");
  return data;
};

/** Get knowledge graph status. */
export const getGraphStatus = async () => {
  const { data } = await api.get("/knowledge-graph/status");
  return data;
};

/** Get zone subgraph. */
export const getZoneGraph = async (zone) => {
  const { data } = await api.get(`/knowledge-graph/zone/${encodeURIComponent(zone)}`);
  return data;
};

/** Get equipment neighborhood graph. */
export const getEquipmentGraph = async (equipment) => {
  const { data } = await api.get(`/knowledge-graph/equipment/${encodeURIComponent(equipment)}`);
  return data;
};

/** Get incident neighborhood graph. */
export const getIncidentGraph = async (incident) => {
  const { data } = await api.get(`/knowledge-graph/incident/${encodeURIComponent(incident)}`);
  return data;
};

/** Search graph nodes. */
export const searchGraph = async (query, nodeType) => {
  const params = { q: query };
  if (nodeType) params.node_type = nodeType;
  const { data } = await api.get("/knowledge-graph/search", { params });
  return data;
};

// ── Agent Orchestrator API ────────────────────────────────

/** Run multi-agent analysis for a zone. */
export const runAgentAnalysis = async (zone, includeSummary = true, agentsToRun = null) => {
  const body = { zone, include_summary: includeSummary };
  if (agentsToRun) body.agents_to_run = agentsToRun;
  const { data } = await api.post("/agent-analysis", body);
  return data;
};

// ── Compliance & Emergency API ────────────────────────────

/** Run compliance analysis for a zone. */
export const runComplianceAnalysis = async (zone) => {
  const { data } = await api.post("/compliance-analysis", { zone });
  return data;
};

/** Generate emergency response plan for a zone. */
export const generateEmergencyResponse = async (zone) => {
  const { data } = await api.post("/emergency-response", { zone });
  return data;
};

/** Auto-generate an incident report for a zone. */
export const generateIncidentReport = async (zone) => {
  const { data } = await api.post("/generate-incident-report", { zone });
  return data;
};

/** Retrieve a stored incident report. */
export const getReport = async (reportId) => {
  const { data } = await api.get(`/reports/${encodeURIComponent(reportId)}`);
  return data;
};

export default api;



