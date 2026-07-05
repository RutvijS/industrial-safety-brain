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

export default api;
