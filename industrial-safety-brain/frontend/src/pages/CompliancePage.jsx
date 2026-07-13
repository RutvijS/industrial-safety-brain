import { useState } from "react";
import { runComplianceAnalysis } from "../services/api";
import "../Phase8.css";

const ZONES = ["Zone A", "Zone B", "Zone C", "Zone D"];

function CompliancePage() {
  const [zone, setZone] = useState("Zone A");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRun = () => {
    setLoading(true); setError(null); setResult(null);
    runComplianceAnalysis(zone)
      .then(setResult)
      .catch((e) => setError(e.response?.data?.detail || "Failed"))
      .finally(() => setLoading(false));
  };

  const scoreClass = result
    ? result.compliance_score >= 80 ? "ok" : result.compliance_score >= 50 ? "warn" : "bad"
    : "ok";

  return (
    <main className="phase8-page">
      <header className="phase8-page__header">
        <div className="phase8-page__logo">📋</div>
        <h1 className="phase8-page__title">Compliance Intelligence</h1>
        <p className="phase8-page__subtitle">Regulatory Compliance Analysis</p>
      </header>

      <div className="phase8-controls">
        <select value={zone} onChange={(e) => setZone(e.target.value)} className="phase8-select">
          {ZONES.map((z) => <option key={z} value={z}>{z}</option>)}
        </select>
        <button className="phase8-btn phase8-btn--teal" onClick={handleRun} disabled={loading}>
          {loading ? "Analyzing..." : "Run Compliance Analysis"}
        </button>
      </div>

      {loading && <div className="phase8-state"><div className="phase8-spinner" /><p>Checking regulations...</p></div>}
      {error && <div className="phase8-state phase8-state--error"><p>{error}</p></div>}

      {!loading && result && (
        <div className="phase8-results">
          {/* Score Card */}
          <div className="p8-score-card">
            <div className={`p8-score-card__circle p8-score-card__circle--${scoreClass}`}>
              {result.compliance_score}
            </div>
            <div className="p8-score-card__info">
              <div className="p8-score-card__status">{result.overall_status}</div>
              <div className="p8-score-card__meta">
                {result.zone} — {result.zone_name} | Risk: {result.risk_level} ({result.risk_score}/100)
              </div>
              <div className="p8-score-card__meta">
                {result.total_findings} violations | {result.critical_findings} critical
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="p8-stats">
            <div className="p8-stat"><span className="p8-stat__label">Score</span><span className={`p8-stat__value ${scoreClass === 'bad' ? 'p8-stat__value--warn' : 'p8-stat__value--ok'}`}>{result.compliance_score}/100</span></div>
            <div className="p8-stat"><span className="p8-stat__label">Violations</span><span className="p8-stat__value p8-stat__value--warn">{result.total_findings}</span></div>
            <div className="p8-stat"><span className="p8-stat__label">Critical</span><span className="p8-stat__value p8-stat__value--warn">{result.critical_findings}</span></div>
            <div className="p8-stat"><span className="p8-stat__label">Compliant</span><span className="p8-stat__value p8-stat__value--ok">{result.compliant_regulations.length}</span></div>
          </div>

          {/* Audit Summary */}
          {result.audit_summary && (
            <Section title="Audit Summary" icon="📝" defaultOpen>
              <div className="p8-summary">{result.audit_summary}</div>
            </Section>
          )}

          {/* Violated Regulations */}
          {result.violated_regulations.length > 0 && (
            <Section title="Violated Regulations" icon="⚠️" count={result.violated_regulations.length} defaultOpen>
              {result.violated_regulations.map((v, i) => (
                <div key={i} className="p8-item">
                  <span className={`p8-item__badge p8-item__badge--${v.severity.toLowerCase()}`}>{v.severity}</span>
                  <div className="p8-item__text">
                    <strong>{v.regulation}</strong> — {v.section}<br/>
                    <span style={{fontSize:'0.65rem',color:'#94a3b8'}}>{v.description}</span><br/>
                    <span style={{fontSize:'0.6rem',color:'#64748b'}}>Evidence: {v.evidence}</span>
                  </div>
                  <span className={`p8-item__badge p8-item__badge--${v.status.toLowerCase().replace(' ','-').replace('_','-')}`}>{v.status}</span>
                </div>
              ))}
            </Section>
          )}

          {/* Corrective Actions */}
          {result.corrective_actions.length > 0 && (
            <Section title="Corrective Actions" icon="🔧" count={result.corrective_actions.length}>
              {result.corrective_actions.map((a, i) => (
                <div key={i} className="p8-item">
                  <span className={`p8-item__badge p8-item__badge--${a.priority.toLowerCase()}`}>{a.priority}</span>
                  <div className="p8-item__text">
                    {a.action}
                    <span style={{display:'block',fontSize:'0.6rem',color:'#64748b'}}>{a.regulation} • {a.deadline_hours}h deadline • {a.responsible}</span>
                  </div>
                </div>
              ))}
            </Section>
          )}

          {/* Compliant */}
          {result.compliant_regulations.length > 0 && (
            <Section title="Compliant Regulations" icon="✅" count={result.compliant_regulations.length}>
              {result.compliant_regulations.map((c, i) => (
                <div key={i} className="p8-item">
                  <span className="p8-item__badge p8-item__badge--compliant">✓</span>
                  <div className="p8-item__text">{c.regulation} — {c.section}</div>
                </div>
              ))}
            </Section>
          )}
        </div>
      )}
    </main>
  );
}

function Section({ title, icon, count, defaultOpen, children }) {
  const [open, setOpen] = useState(defaultOpen || false);
  return (
    <section className="p8-section">
      <button className="p8-section__header" onClick={() => setOpen(!open)}>
        <span className="p8-section__icon">{icon}</span>
        <span className="p8-section__title">{title}</span>
        {count !== undefined && <span className="p8-section__count">{count}</span>}
        <span className="p8-section__chevron">{open ? "▼" : "▶"}</span>
      </button>
      {open && <div className="p8-section__body">{children}</div>}
    </section>
  );
}

export default CompliancePage;
