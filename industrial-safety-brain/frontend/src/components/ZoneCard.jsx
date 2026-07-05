/**
 * ZoneCard — Displays the unified state for a single zone.
 *
 * Props:
 *   zone - A ZoneState object from the /plant-state API
 */

import { useState } from "react";

function Section({ title, icon, count, defaultOpen, children }) {
  const [open, setOpen] = useState(defaultOpen || false);

  return (
    <div className="zone-card__section">
      <button
        className="zone-card__section-header"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span className="zone-card__section-icon">{icon}</span>
        <span className="zone-card__section-title">{title}</span>
        {count !== undefined && (
          <span className="zone-card__section-count">{count}</span>
        )}
        <span className={`zone-card__chevron ${open ? "zone-card__chevron--open" : ""}`}>
          &#9660;
        </span>
      </button>
      {open && <div className="zone-card__section-body">{children}</div>}
    </div>
  );
}

function HazardBadge({ level }) {
  const cls =
    level === "Critical" ? "hazard--critical" :
    level === "High" ? "hazard--high" :
    level === "Moderate" ? "hazard--moderate" :
    "hazard--low";
  return <span className={`hazard-badge ${cls}`}>{level}</span>;
}

function ZoneCard({ zone }) {
  const ctx = zone.overall_context;
  const sensor = zone.current_sensor_status;

  return (
    <article className="zone-card">
      {/* Header */}
      <header className="zone-card__header">
        <div className="zone-card__header-left">
          <h2 className="zone-card__zone-name">{zone.zone}</h2>
          <span className="zone-card__zone-label">{zone.zone_name}</span>
        </div>
        <div className="zone-card__header-right">
          <HazardBadge level={ctx.hazard_level} />
          <span className="zone-card__risk-type">{zone.risk_type}</span>
        </div>
      </header>

      {/* Quick stats */}
      <div className="zone-card__stats">
        <div className="zone-card__stat">
          <span className="zone-card__stat-value">{ctx.worker_count}</span>
          <span className="zone-card__stat-label">Workers</span>
        </div>
        <div className="zone-card__stat">
          <span className="zone-card__stat-value">{ctx.active_permit_count}</span>
          <span className="zone-card__stat-label">Permits</span>
        </div>
        <div className="zone-card__stat">
          <span className="zone-card__stat-value">{ctx.active_maintenance_count}</span>
          <span className="zone-card__stat-label">Maint.</span>
        </div>
        <div className="zone-card__stat">
          <span className="zone-card__stat-value zone-card__stat-value--critical">
            {ctx.critical_sensor_count}
          </span>
          <span className="zone-card__stat-label">Critical</span>
        </div>
        <div className="zone-card__stat">
          <span className="zone-card__stat-value">{ctx.high_risk_operations}</span>
          <span className="zone-card__stat-label">High Risk</span>
        </div>
      </div>

      {/* Sensor Summary */}
      <Section title="Sensor Status" icon="📡" count={sensor.total_readings} defaultOpen={true}>
        <div className="zone-card__sensor-grid">
          <div className="zone-card__sensor-item">
            <span className="zone-card__sensor-label">Avg Gas</span>
            <span className="zone-card__sensor-value">{sensor.avg_gas_level} ppm</span>
          </div>
          <div className="zone-card__sensor-item">
            <span className="zone-card__sensor-label">Avg Temp</span>
            <span className="zone-card__sensor-value">{sensor.avg_temperature} C</span>
          </div>
          <div className="zone-card__sensor-item">
            <span className="zone-card__sensor-label">Avg Pressure</span>
            <span className="zone-card__sensor-value">{sensor.avg_pressure} bar</span>
          </div>
          <div className="zone-card__sensor-item">
            <span className="zone-card__sensor-label">Avg Humidity</span>
            <span className="zone-card__sensor-value">{sensor.avg_humidity}%</span>
          </div>
        </div>
        <div className="zone-card__sensor-status-row">
          <span className="badge badge--normal">{sensor.normal_count} Normal</span>
          <span className="badge badge--warning">{sensor.warning_count} Warning</span>
          <span className="badge badge--critical">{sensor.critical_count} Critical</span>
        </div>
      </Section>

      {/* Active Permits */}
      <Section title="Active Permits" icon="📋" count={zone.active_permits.length}>
        {zone.active_permits.length === 0 ? (
          <p className="zone-card__empty">No active permits</p>
        ) : (
          <ul className="zone-card__list">
            {zone.active_permits.map((p) => (
              <li key={p.permit_id} className="zone-card__list-item">
                <span className="zone-card__list-id">{p.permit_id}</span>
                <span className="zone-card__list-detail">{p.permit_type}</span>
                <span className="zone-card__list-detail">{p.equipment}</span>
                <span className={`badge ${p.status === "Approved" ? "badge--normal" : "badge--warning"}`}>
                  {p.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      {/* Active Maintenance */}
      <Section title="Maintenance" icon="🔧" count={zone.active_maintenance.length}>
        {zone.active_maintenance.length === 0 ? (
          <p className="zone-card__empty">No active maintenance</p>
        ) : (
          <ul className="zone-card__list">
            {zone.active_maintenance.map((m) => (
              <li key={m.maintenance_id} className="zone-card__list-item">
                <span className="zone-card__list-id">{m.maintenance_id}</span>
                <span className="zone-card__list-detail">{m.maintenance_type}</span>
                <span className="zone-card__list-detail">{m.equipment}</span>
                <span className={`badge ${
                  m.status === "Overdue" ? "badge--critical" :
                  m.status === "In Progress" ? "badge--warning" :
                  "badge--muted"
                }`}>
                  {m.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      {/* Current Shift */}
      <Section title="Current Shift" icon="👷">
        {zone.current_shift ? (
          <div className="zone-card__shift">
            <div className="zone-card__shift-row">
              <span className="zone-card__shift-label">Shift:</span>
              <span>{zone.current_shift.shift_name}</span>
            </div>
            <div className="zone-card__shift-row">
              <span className="zone-card__shift-label">Supervisor:</span>
              <span>{zone.current_shift.supervisor}</span>
            </div>
            <div className="zone-card__shift-row">
              <span className="zone-card__shift-label">Workers:</span>
              <span>{zone.current_shift.workers.join(", ")}</span>
            </div>
          </div>
        ) : (
          <p className="zone-card__empty">No shift data</p>
        )}
      </Section>

      {/* Recent Incidents */}
      <Section title="Recent Incidents" icon="⚠️" count={zone.recent_incidents.length}>
        {zone.recent_incidents.length === 0 ? (
          <p className="zone-card__empty">No recent incidents</p>
        ) : (
          <ul className="zone-card__list">
            {zone.recent_incidents.slice(0, 5).map((i) => (
              <li key={i.incident_id} className="zone-card__list-item">
                <span className="zone-card__list-id">{i.incident_id}</span>
                <span className="zone-card__list-detail zone-card__list-detail--wide">
                  {i.description}
                </span>
                <span className={`badge ${
                  i.severity === "Fatal" || i.severity === "Critical" ? "badge--critical" :
                  i.severity === "Serious" ? "badge--warning" :
                  "badge--muted"
                }`}>
                  {i.severity}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Section>
    </article>
  );
}

export default ZoneCard;
