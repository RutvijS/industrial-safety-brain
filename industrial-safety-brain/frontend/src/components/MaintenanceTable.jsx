import { useState, useEffect } from "react";
import DataTable from "./DataTable";
import { getMaintenance } from "../services/api";

const COLUMNS = [
  { key: "maintenance_id", label: "ID" },
  { key: "equipment", label: "Equipment" },
  { key: "zone", label: "Zone" },
  { key: "maintenance_type", label: "Type" },
  { key: "assigned_engineer", label: "Engineer" },
  {
    key: "status",
    label: "Status",
    render: (v) => {
      const cls =
        v === "Completed" ? "badge--normal" :
        v === "Overdue" ? "badge--critical" :
        v === "In Progress" ? "badge--warning" :
        "badge--muted";
      return <span className={`badge ${cls}`}>{v}</span>;
    },
  },
  { key: "scheduled_time", label: "Scheduled", render: (v) => v?.replace("T", " ").slice(0, 16) },
  { key: "completion_time", label: "Completed", render: (v) => v ? v.replace("T", " ").slice(0, 16) : "-" },
  { key: "remarks", label: "Remarks" },
];

function MaintenanceTable() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getMaintenance()
      .then(setData)
      .catch((err) => setError(err.response?.data?.detail || "Failed to load maintenance data"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <DataTable
      columns={COLUMNS}
      data={data}
      loading={loading}
      error={error}
      title="Maintenance Activities"
      icon="🔧"
    />
  );
}

export default MaintenanceTable;
