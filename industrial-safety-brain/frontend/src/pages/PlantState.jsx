import { useState, useEffect } from "react";
import ZoneCard from "../components/ZoneCard";
import { getPlantState, getPlantOverviewSummary } from "../services/api";
import "../PlantState.css";

function PlantState() {
  const [plantState, setPlantState] = useState(null);
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([getPlantState(), getPlantOverviewSummary()])
      .then(([state, summary]) => {
        setPlantState(state);
        setOverview(summary);
      })
      .catch((err) => setError(err.response?.data?.detail || "Failed to load plant state"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="plant-state">
      <header className="plant-state__header">
        <div className="plant-state__logo">🧠</div>
        <h1 className="plant-state__title">Plant State</h1>
        <p className="plant-state__subtitle">Unified Safety Intelligence Layer</p>
      </header>

      {/* Overview Summary Bar */}
      {overview && !loading && !error && (
        <div className="plant-state__summary-bar">
          <div className="summary-stat">
            <span className="summary-stat__value">{overview.zone_count}</span>
            <span className="summary-stat__label">Zones</span>
          </div>
          <div className="summary-stat">
            <span className="summary-stat__value">{overview.active_permits}</span>
            <span className="summary-stat__label">Active Permits</span>
          </div>
          <div className="summary-stat">
            <span className="summary-stat__value">{overview.maintenance_jobs}</span>
            <span className="summary-stat__label">Maintenance</span>
          </div>
          <div className="summary-stat summary-stat--critical">
            <span className="summary-stat__value">{overview.critical_sensors}</span>
            <span className="summary-stat__label">Critical Sensors</span>
          </div>
          <div className="summary-stat summary-stat--warning">
            <span className="summary-stat__value">{overview.warning_sensors}</span>
            <span className="summary-stat__label">Warnings</span>
          </div>
          <div className="summary-stat">
            <span className="summary-stat__value">{overview.recent_incidents}</span>
            <span className="summary-stat__label">Incidents</span>
          </div>
          <div className="summary-stat">
            <span className="summary-stat__value">{overview.total_workers_on_shift}</span>
            <span className="summary-stat__label">Workers</span>
          </div>
        </div>
      )}

      {/* Loading / Error / Data */}
      {loading && (
        <div className="plant-state__state">
          <div className="plant-state__spinner" />
          <p>Loading plant state...</p>
        </div>
      )}

      {error && (
        <div className="plant-state__state plant-state__state--error">
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && plantState && (
        <div className="plant-state__zones">
          {plantState.zones.map((zone) => (
            <ZoneCard key={zone.zone} zone={zone} />
          ))}
        </div>
      )}

      {!loading && !error && (!plantState || plantState.zones.length === 0) && (
        <div className="plant-state__state">
          <p>No zone data available</p>
        </div>
      )}
    </main>
  );
}

export default PlantState;
