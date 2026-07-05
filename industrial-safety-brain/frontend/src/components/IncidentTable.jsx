import { useState, useEffect } from "react";
import DataTable from "./DataTable";
import { getIncidents } from "../services/api";

const COLUMNS = [
  { key: "incident_id", label: "ID" },
  { key: "date", label: "Date", render: (v) => v?.replace("T", " ").slice(0, 16) },
  { key: "zone", label: "Zone" },
  { key: "equipment", label: "Equipment" },
  { key: "description", label: "Description" },
  { key: "root_cause", label: "Root Cause" },
  {
    key: "severity",
    label: "Severity",
    render: (v) => {
      const cls =
        v === "Fatal" || v === "Critical" ? "badge--critical" :
        v === "Serious" ? "badge--warning" :
        "badge--muted";
      return <span className={`badge ${cls}`}>{v}</span>;
    },
  },
  { key: "injuries", label: "Injuries" },
  { key: "corrective_action", label: "Corrective Action" },
];

function IncidentTable() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getIncidents()
      .then(setData)
      .catch((err) => setError(err.response?.data?.detail || "Failed to load incident data"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <DataTable
      columns={COLUMNS}
      data={data}
      loading={loading}
      error={error}
      title="Historical Incidents"
      icon="⚠️"
    />
  );
}

export default IncidentTable;
