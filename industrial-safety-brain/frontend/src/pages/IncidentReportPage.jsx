import { useState } from "react";
import { generateIncidentReport } from "../services/api";
import "../Phase8.css";

const ZONES = ["Zone A", "Zone B", "Zone C", "Zone D"];

function IncidentReportPage() {
  const [zone, setZone] = useState("Zone A");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerate = () => {
    setLoading(true); setError(null); setReport(null);
    generateIncidentReport(zone)
      .then(setReport)
      .catch((e) => setError(e.response?.data?.detail || "Failed"))
      .finally(() => setLoading(false));
  };

  const handlePrint = () => window.print();

  return (
    <main className="phase8-page">
      <header className="phase8-page__header">
        <div className="phase8-page__logo" style={{filter:'drop-shadow(0 0 12px rgba(59,130,246,0.4))'}}>📄</div>
        <h1 className="phase8-page__title phase8-page__title--blue">Incident Report</h1>
        <p className="phase8-page__subtitle">Auto-Generated Safety Report</p>
      </header>

      <div className="phase8-controls">
        <select value={zone} onChange={(e) => setZone(e.target.value)} className="phase8-select">
          {ZONES.map((z) => <option key={z} value={z}>{z}</option>)}
        </select>
        <button className="phase8-btn phase8-btn--blue" onClick={handleGenerate} disabled={loading}>
          {loading ? "Generating..." : "Generate Incident Report"}
        </button>
        {report && (
          <button className="phase8-btn phase8-btn--print" onClick={handlePrint}>🖨️ Print</button>
        )}
      </div>

      {loading && <div className="phase8-state"><div className="phase8-spinner" style={{borderTopColor:'#3b82f6'}} /><p>Generating report...</p></div>}
      {error && <div className="phase8-state phase8-state--error"><p>{error}</p></div>}

      {!loading && report && (
        <div className="phase8-results">
          {/* Report Header */}
          <div className="p8-report-section">
            <h3>Report Information</h3>
            <div className="p8-stats">
              <div className="p8-stat"><span className="p8-stat__label">Report ID</span><span className="p8-stat__value" style={{fontSize:'0.75rem'}}>{report.report_id}</span></div>
              <div className="p8-stat"><span className="p8-stat__label">Zone</span><span className="p8-stat__value" style={{fontSize:'0.85rem'}}>{report.zone_name}</span></div>
              <div className="p8-stat"><span className="p8-stat__label">Risk Level</span><span className={`p8-stat__value ${report.risk_level === 'CRITICAL' || report.risk_level === 'HIGH' ? 'p8-stat__value--warn' : ''}`}>{report.risk_level}</span></div>
              <div className="p8-stat"><span className="p8-stat__label">Risk Score</span><span className="p8-stat__value">{report.risk_score}/100</span></div>
            </div>
            <div className="p8-stats" style={{marginTop:'0.3rem'}}>
              <div className="p8-stat"><span className="p8-stat__label">Priority</span><span className="p8-stat__value p8-stat__value--warn">{report.emergency_priority}</span></div>
              <div className="p8-stat"><span className="p8-stat__label">Workers</span><span className="p8-stat__value">{report.worker_count}</span></div>
              <div className="p8-stat"><span className="p8-stat__label">Permits</span><span className="p8-stat__value">{report.active_permits}</span></div>
              <div className="p8-stat"><span className="p8-stat__label">Evacuation</span><span className={`p8-stat__value ${report.evacuation_required ? 'p8-stat__value--warn' : 'p8-stat__value--ok'}`}>{report.evacuation_required ? 'YES' : 'No'}</span></div>
            </div>
          </div>

          {/* Executive Summary */}
          <div className="p8-report-section">
            <h3>Executive Summary</h3>
            <div className="p8-summary p8-summary--blue">{report.executive_summary}</div>
          </div>

          {/* Equipment */}
          {report.equipment_involved.length > 0 && (
            <div className="p8-report-section">
              <h3>Equipment Involved ({report.equipment_involved.length})</h3>
              <div className="p8-ppe">
                {report.equipment_involved.map((eq, i) => (
                  <div key={i} className="p8-ppe-item"><span className="p8-ppe-item__name">⚙️ {eq}</span></div>
                ))}
              </div>
            </div>
          )}

          {/* Detected Risks */}
          {report.detected_risks.length > 0 && (
            <div className="p8-report-section">
              <h3>Detected Risks ({report.detected_risks.length})</h3>
              {report.detected_risks.map((r, i) => (
                <div key={i} className="p8-item">
                  <span className={`p8-item__badge p8-item__badge--${r.severity?.toLowerCase()}`}>{r.severity}</span>
                  <div className="p8-item__text"><strong>{r.name}</strong><br/><span style={{fontSize:'0.6rem',color:'#94a3b8'}}>{r.description}</span></div>
                </div>
              ))}
            </div>
          )}

          {/* Risk Factors */}
          {report.risk_factors.length > 0 && (
            <div className="p8-report-section">
              <h3>Risk Factors ({report.risk_factors.length})</h3>
              {report.risk_factors.map((f, i) => (
                <div key={i} className="p8-item">
                  <span className={`p8-item__badge p8-item__badge--${f.status?.toLowerCase()}`}>{f.status}</span>
                  <div className="p8-item__text">{f.name.replace(/_/g,' ')}: {f.value}</div>
                  <span className="p8-item__meta">Score: {f.score?.toFixed(0)}</span>
                </div>
              ))}
            </div>
          )}

          {/* Evidence */}
          {report.evidence.length > 0 && (
            <div className="p8-report-section">
              <h3>Evidence ({report.evidence.length})</h3>
              {report.evidence.map((e, i) => (
                <div key={i} className="p8-item">
                  <span className="p8-item__badge p8-item__badge--medium">{e.type}</span>
                  <div className="p8-item__text"><strong>{e.source}</strong><br/><span style={{fontSize:'0.6rem',color:'#94a3b8'}}>{e.detail}</span></div>
                </div>
              ))}
            </div>
          )}

          {/* Regulations */}
          {report.applicable_regulations.length > 0 && (
            <div className="p8-report-section">
              <h3>Applicable Regulations ({report.applicable_regulations.length})</h3>
              {report.applicable_regulations.map((r, i) => (
                <div key={i} className="p8-item">
                  <span className="p8-item__badge p8-item__badge--warning">REG</span>
                  <div className="p8-item__text"><strong>{r.regulation}</strong> — {r.section}</div>
                </div>
              ))}
            </div>
          )}

          {/* Corrective Actions */}
          {report.corrective_actions.length > 0 && (
            <div className="p8-report-section">
              <h3>Corrective Actions ({report.corrective_actions.length})</h3>
              {report.corrective_actions.map((a, i) => (
                <div key={i} className="p8-item">
                  <span className={`p8-item__badge p8-item__badge--${a.priority?.toLowerCase()}`}>{a.priority}</span>
                  <div className="p8-item__text">{a.action}<br/><span style={{fontSize:'0.6rem',color:'#64748b'}}>{a.reasoning}</span></div>
                </div>
              ))}
            </div>
          )}

          {/* Timestamp */}
          <div style={{textAlign:'center',fontSize:'0.65rem',color:'#475569',padding:'0.5rem'}}>
            Generated: {report.timestamp} | Format: {report.export_format.toUpperCase()}
          </div>
        </div>
      )}
    </main>
  );
}

export default IncidentReportPage;
