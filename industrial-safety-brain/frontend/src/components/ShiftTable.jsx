import { useState, useEffect } from "react";
import DataTable from "./DataTable";
import { getShifts } from "../services/api";

const COLUMNS = [
  { key: "shift_id", label: "ID" },
  { key: "shift_name", label: "Shift" },
  { key: "zone", label: "Zone" },
  { key: "supervisor", label: "Supervisor" },
  { key: "workers", label: "Workers", render: (v) => Array.isArray(v) ? v.join(", ") : v },
  { key: "start_time", label: "Start", render: (v) => v?.replace("T", " ").slice(0, 16) },
  { key: "end_time", label: "End", render: (v) => v?.replace("T", " ").slice(0, 16) },
];

function ShiftTable() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getShifts()
      .then(setData)
      .catch((err) => setError(err.response?.data?.detail || "Failed to load shift data"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <DataTable
      columns={COLUMNS}
      data={data}
      loading={loading}
      error={error}
      title="Shift Schedules"
      icon="👷"
    />
  );
}

export default ShiftTable;
