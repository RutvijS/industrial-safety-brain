import { useState, useEffect } from "react";
import DataTable from "./DataTable";
import { getSensors } from "../services/api";

const COLUMNS = [
  { key: "sensor_id", label: "ID" },
  { key: "timestamp", label: "Timestamp", render: (v) => v?.replace("T", " ").slice(0, 19) },
  { key: "zone", label: "Zone" },
  { key: "equipment", label: "Equipment" },
  { key: "gas_level", label: "Gas (ppm)" },
  { key: "temperature", label: "Temp (C)" },
  { key: "pressure", label: "Pressure (bar)" },
  { key: "humidity", label: "Humidity (%)" },
  { key: "vibration", label: "Vibration (mm/s)" },
  {
    key: "status",
    label: "Status",
    render: (v) => {
      const cls = v === "Critical" ? "badge--critical" : v === "Warning" ? "badge--warning" : "badge--normal";
      return <span className={`badge ${cls}`}>{v}</span>;
    },
  },
];

function SensorTable() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getSensors()
      .then(setData)
      .catch((err) => setError(err.response?.data?.detail || "Failed to load sensor data"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <DataTable
      columns={COLUMNS}
      data={data}
      loading={loading}
      error={error}
      title="Sensor Readings"
      icon="📡"
    />
  );
}

export default SensorTable;
