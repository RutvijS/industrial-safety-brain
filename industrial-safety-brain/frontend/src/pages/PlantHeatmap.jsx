import { useState, useEffect, useRef, useCallback } from "react";
import { getPlantLayout, getHeatmapData, getZoneDetails } from "../services/api";
import "../PlantHeatmap.css";

const REFRESH_INTERVAL = 10_000; // 10 seconds

function PlantHeatmap() {
  const [layout, setLayout] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [selectedZone, setSelectedZone] = useState(null);
  const [zoneDetails, setZoneDetails] = useState(null);
  const [hoveredZone, setHoveredZone] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const timerRef = useRef(null);

  // Fetch layout once on mount
  useEffect(() => {
    getPlantLayout()
      .then(setLayout)
      .catch(() => setError("Failed to load plant layout"));
  }, []);

  // Fetch heatmap data and auto-refresh
  const fetchHeatmap = useCallback(() => {
    getHeatmapData()
      .then((data) => {
        setHeatmap(data);
        setLoading(false);
        setError(null);
      })
      .catch(() => {
        setError("Failed to load heatmap data");
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchHeatmap();
    timerRef.current = setInterval(fetchHeatmap, REFRESH_INTERVAL);
    return () => clearInterval(timerRef.current);
  }, [fetchHeatmap]);

  // Fetch zone details when a zone is selected
  const handleZoneClick = (zoneId) => {
    const zoneKey = `Zone ${zoneId}`;
    if (selectedZone === zoneKey) {
      setSelectedZone(null);
      setZoneDetails(null);
      return;
    }
    setSelectedZone(zoneKey);
    setDetailsLoading(true);
    getZoneDetails(zoneKey)
      .then((data) => {
        setZoneDetails(data);
        setDetailsLoading(false);
      })
      .catch(() => {
        setZoneDetails(null);
        setDetailsLoading(false);
      });
  };

  // Get heatmap data for a specific zone
  const getZoneHeatmap = (zoneId) => {
    if (!heatmap) return null;
    return heatmap.zones.find((z) => z.zone === `Zone ${zoneId}`);
  };

  if (loading && !heatmap) {
    return (
      <main className="heatmap-page">
        <div className="heatmap-page__state">
          <div className="heatmap-page__spinner" />
          <p>Loading plant heatmap...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="heatmap-page">
      <header className="heatmap-page__header">
        <div className="heatmap-page__logo">🗺️</div>
        <h1 className="heatmap-page__title">Plant Heatmap</h1>
        <p className="heatmap-page__subtitle">Geospatial Safety Intelligence</p>
      </header>

      {error && (
        <div className="heatmap-page__state heatmap-page__state--error">
          <p>{error}</p>
        </div>
      )}

      {/* Overall Status Bar */}
      {heatmap && (
        <div className="heatmap-page__status-bar">
          <span className={`heatmap-status heatmap-status--${heatmap.overall_risk.toLowerCase()}`}>
            Overall: {heatmap.overall_risk}
          </span>
          <span className="heatmap-status__score">
            Highest Score: {heatmap.overall_risk_score}/100
          </span>
          <span className="heatmap-status__refresh">
            Auto-refresh: 10s
          </span>
        </div>
      )}

      <div className="heatmap-page__content">
        {/* Plant Map */}
        <div className="heatmap-page__map-container">
          <svg
            className="heatmap-svg"
            viewBox="0 0 680 520"
            preserveAspectRatio="xMidYMid meet"
          >
            {/* Grid background */}
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(148,163,184,0.06)" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="680" height="520" fill="url(#grid)" />

            {/* Zone rectangles */}
            {layout && layout.zones.map((zone) => {
              const zoneHeatmap = getZoneHeatmap(zone.id);
              const color = zoneHeatmap ? zoneHeatmap.color : "#334155";
              const isSelected = selectedZone === `Zone ${zone.id}`;
              const isHovered = hoveredZone === zone.id;

              return (
                <g key={zone.id}>
                  {/* Zone rect */}
                  <rect
                    x={zone.x}
                    y={zone.y}
                    width={zone.width}
                    height={zone.height}
                    rx={12}
                    fill={color}
                    fillOpacity={isHovered ? 0.35 : 0.2}
                    stroke={isSelected ? "#e2e8f0" : color}
                    strokeWidth={isSelected ? 2.5 : 1.5}
                    className="heatmap-zone-rect"
                    onClick={() => handleZoneClick(zone.id)}
                    onMouseEnter={() => setHoveredZone(zone.id)}
                    onMouseLeave={() => setHoveredZone(null)}
                  />
                  {/* Zone label */}
                  <text
                    x={zone.x + zone.width / 2}
                    y={zone.y + 28}
                    textAnchor="middle"
                    className="heatmap-zone-label"
                    onClick={() => handleZoneClick(zone.id)}
                    onMouseEnter={() => setHoveredZone(zone.id)}
                    onMouseLeave={() => setHoveredZone(null)}
                  >
                    Zone {zone.id}
                  </text>
                  {/* Zone name */}
                  <text
                    x={zone.x + zone.width / 2}
                    y={zone.y + 48}
                    textAnchor="middle"
                    className="heatmap-zone-name"
                  >
                    {zone.name}
                  </text>
                  {/* Risk score */}
                  {zoneHeatmap && (
                    <>
                      <text
                        x={zone.x + zone.width / 2}
                        y={zone.y + zone.height / 2 + 10}
                        textAnchor="middle"
                        className="heatmap-zone-score"
                        fill={color}
                      >
                        {zoneHeatmap.risk_score}
                      </text>
                      <text
                        x={zone.x + zone.width / 2}
                        y={zone.y + zone.height / 2 + 28}
                        textAnchor="middle"
                        className="heatmap-zone-level"
                        fill={color}
                      >
                        {zoneHeatmap.risk_level}
                      </text>
                    </>
                  )}
                  {/* Quick stats at bottom */}
                  {zoneHeatmap && (
                    <text
                      x={zone.x + zone.width / 2}
                      y={zone.y + zone.height - 12}
                      textAnchor="middle"
                      className="heatmap-zone-stats"
                    >
                      🌡{zoneHeatmap.avg_temperature.toFixed(0)}° 💨{zoneHeatmap.avg_gas_level.toFixed(0)}ppm ⚡{zoneHeatmap.avg_pressure.toFixed(1)}bar
                    </text>
                  )}
                </g>
              );
            })}
          </svg>

          {/* Hover Tooltip */}
          {hoveredZone && !selectedZone && (() => {
            const zh = getZoneHeatmap(hoveredZone);
            if (!zh) return null;
            return (
              <div className="heatmap-tooltip">
                <div className="heatmap-tooltip__header">{zh.zone} — {zh.zone_name}</div>
                <div className="heatmap-tooltip__row">Risk: <strong>{zh.risk_level}</strong> ({zh.risk_score}/100)</div>
                <div className="heatmap-tooltip__row">🌡 Temperature: {zh.avg_temperature.toFixed(1)}°C</div>
                <div className="heatmap-tooltip__row">💨 Gas Level: {zh.avg_gas_level.toFixed(1)} ppm</div>
                <div className="heatmap-tooltip__row">⚡ Pressure: {zh.avg_pressure.toFixed(2)} bar</div>
                <div className="heatmap-tooltip__row">👷 Workers: {zh.worker_count}</div>
                <div className="heatmap-tooltip__hint">Click for details</div>
              </div>
            );
          })()}

          {/* Legend */}
          <div className="heatmap-legend">
            <span className="heatmap-legend__title">Risk Level</span>
            <div className="heatmap-legend__items">
              <span className="heatmap-legend__item"><span className="heatmap-legend__dot" style={{background:"#22c55e"}}/>Low</span>
              <span className="heatmap-legend__item"><span className="heatmap-legend__dot" style={{background:"#eab308"}}/>Medium</span>
              <span className="heatmap-legend__item"><span className="heatmap-legend__dot" style={{background:"#f97316"}}/>High</span>
              <span className="heatmap-legend__item"><span className="heatmap-legend__dot" style={{background:"#ef4444"}}/>Critical</span>
            </div>
          </div>
        </div>

        {/* Side Panel */}
        {selectedZone && (
          <aside className="heatmap-panel">
            <button className="heatmap-panel__close" onClick={() => { setSelectedZone(null); setZoneDetails(null); }}>✕</button>

            {detailsLoading && (
              <div className="heatmap-panel__loading">
                <div className="heatmap-page__spinner" />
                <p>Loading zone details...</p>
              </div>
            )}

            {!detailsLoading && zoneDetails && (
              <>
                {/* Header */}
                <div className="heatmap-panel__header">
                  <h2>{zoneDetails.zone}</h2>
                  <span className="heatmap-panel__zone-name">{zoneDetails.zone_name}</span>
                  <span className="heatmap-panel__risk-type">{zoneDetails.risk_type}</span>
                </div>

                {/* Risk Score */}
                <div className={`heatmap-panel__score heatmap-panel__score--${zoneDetails.risk_level.toLowerCase()}`}>
                  <span className="heatmap-panel__score-value">{zoneDetails.risk_score}</span>
                  <span className="heatmap-panel__score-label">/ 100 — {zoneDetails.risk_level}</span>
                </div>

                {/* Sensors */}
                <PanelSection title="Current Sensors">
                  <div className="panel-stats">
                    <PanelStat label="Temperature" value={`${zoneDetails.avg_temperature.toFixed(1)}°C`} />
                    <PanelStat label="Gas Level" value={`${zoneDetails.avg_gas_level.toFixed(1)} ppm`} />
                    <PanelStat label="Pressure" value={`${zoneDetails.avg_pressure.toFixed(2)} bar`} />
                    <PanelStat label="Humidity" value={`${zoneDetails.avg_humidity.toFixed(1)}%`} />
                    <PanelStat label="Vibration" value={`${zoneDetails.avg_vibration.toFixed(2)} mm/s`} />
                    <PanelStat label="Critical" value={zoneDetails.critical_sensors} warn />
                    <PanelStat label="Warning" value={zoneDetails.warning_sensors} />
                  </div>
                </PanelSection>

                {/* Risk Factors */}
                {zoneDetails.risk_factors.length > 0 && (
                  <PanelSection title="Risk Factors">
                    {zoneDetails.risk_factors.map((f, i) => (
                      <div key={i} className="panel-factor">
                        <span className="panel-factor__name">{f.name.replace(/_/g, " ")}</span>
                        <div className="panel-factor__bar-bg">
                          <div
                            className={`panel-factor__bar panel-factor__bar--${f.status.toLowerCase()}`}
                            style={{ width: `${Math.min(f.normalized_score, 100)}%` }}
                          />
                        </div>
                        <span className="panel-factor__value">{f.normalized_score.toFixed(0)}</span>
                      </div>
                    ))}
                  </PanelSection>
                )}

                {/* Detected Risks */}
                {zoneDetails.detected_risks.length > 0 && (
                  <PanelSection title="Detected Risks">
                    {zoneDetails.detected_risks.map((r, i) => (
                      <div key={i} className="panel-risk">
                        <span className={`panel-risk__severity panel-risk__severity--${r.severity.toLowerCase()}`}>
                          {r.severity}
                        </span>
                        <span className="panel-risk__name">{r.name}</span>
                      </div>
                    ))}
                  </PanelSection>
                )}

                {/* Recommendations */}
                {zoneDetails.recommendations.length > 0 && (
                  <PanelSection title="Recommendations">
                    {zoneDetails.recommendations.map((r, i) => (
                      <div key={i} className="panel-rec">
                        <span className={`panel-rec__priority panel-rec__priority--${r.priority.toLowerCase()}`}>
                          {r.priority}
                        </span>
                        <span className="panel-rec__action">{r.action}</span>
                      </div>
                    ))}
                  </PanelSection>
                )}

                {/* Operations */}
                <PanelSection title="Operations">
                  <div className="panel-stats">
                    <PanelStat label="Active Permits" value={zoneDetails.active_permits} />
                    <PanelStat label="Maintenance" value={zoneDetails.active_maintenance} />
                    <PanelStat label="Incidents" value={zoneDetails.recent_incidents} warn={zoneDetails.recent_incidents > 0} />
                    <PanelStat label="Workers" value={zoneDetails.worker_count} />
                  </div>
                </PanelSection>
              </>
            )}
          </aside>
        )}
      </div>
    </main>
  );
}

/* ── Helpers ── */

function PanelSection({ title, children }) {
  return (
    <section className="heatmap-panel__section">
      <h3 className="heatmap-panel__section-title">{title}</h3>
      {children}
    </section>
  );
}

function PanelStat({ label, value, warn }) {
  return (
    <div className="panel-stat">
      <span className="panel-stat__label">{label}</span>
      <span className={`panel-stat__value ${warn ? "panel-stat__value--warn" : ""}`}>{value}</span>
    </div>
  );
}

export default PlantHeatmap;
