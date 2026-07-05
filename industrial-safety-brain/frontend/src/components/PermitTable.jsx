import { useState, useEffect } from "react";
import DataTable from "./DataTable";
import { getPermits } from "../services/api";

const COLUMNS = [
  { key: "permit_id", label: "ID" },
  { key: "permit_type", label: "Type" },
  { key: "zone", label: "Zone" },
  { key: "equipment", label: "Equipment" },
  { key: "issued_to", label: "Issued To" },
  { key: "approved_by", label: "Approved By" },
  { key: "start_time", label: "Start", render: (v) => v?.replace("T", " ").slice(0, 16) },
  { key: "end_time", label: "End", render: (v) => v?.replace("T", " ").slice(0, 16) },
  {
    key: "status",
    label: "Status",
    render: (v) => {
      const cls =
        v === "Approved" ? "badge--normal" :
        v === "Revoked" ? "badge--critical" :
        v === "Pending" ? "badge--warning" :
        "badge--muted";
      return <span className={`badge ${cls}`}>{v}</span>;
    },
  },
];

function PermitTable() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getPermits()
      .then(setData)
      .catch((err) => setError(err.response?.data?.detail || "Failed to load permit data"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <DataTable
      columns={COLUMNS}
      data={data}
      loading={loading}
      error={error}
      title="Work Permits"
      icon="📋"
    />
  );
}

export default PermitTable;
