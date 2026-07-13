import { useState } from "react";
import { generateEmergencyResponse } from "../services/api";
import "../Phase8.css";

const ZONES = ["Zone A", "Zone B", "Zone C", "Zone D"];

function EmergencyPage() {
  const [zone, setZone] = useState("Zone A");
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerate = () => {
    setLoading(true); setError(null); setPlan(null);
    generateEmergencyResponse(zone)
      .then(setPlan)
      .catch((e) => setError(e.response?.data?.detail || "Failed"))
      .finally(() => setLoading(false));
  };

  return (
    <main className="phase8-page">
      <header className="phase8-page__header">
        <div className="phase8-page__logo" style={{filter:'drop-shadow(0 0 12px rgba(239,68,68,0.4))'}}>🚨</div>
        <h1 className="phase8-page__title phase8-page__title--red">Emergency Response</h1>
        <p className="phase8-page__subtitle">Emergency Response Orchestrator</p>
      </header>

      <div className="phase8-controls">
        <select value={zone} onChange={(e) => setZone(e.target.value)} className="phase8-select">
          {ZONES.map((z) => <option key={z} value={z}>{z}</option>)}
        </select>
        <button className="phase8-btn phase8-btn--red" onClick={handleGenerate} disabled={loading}>
          {loading ? "Generating..." : "Generate Emergency Plan"}
        </button>
      </div>

      {loading && <div className="phase8-state"><div className="phase8-spinner" style={{borderTopColor:'#ef4444'}} /><p>Generating emergency plan...</p></div>}
      {error && <div className="phase8-state phase8-state--error"><p>{error}</p></div>}

      {!loading && plan && (
        <div className="phase8-results">
          {/* Header */}
          <div className="p8-score-card">
            <div className={`p8-score-card__circle p8-score-card__circle--${plan.priority === 'Critical' ? 'bad' : plan.priority === 'High' ? 'warn' : 'ok'}`}>
              {plan.priority === 'Critical' ? '🔴' : plan.priority === 'High' ? '🟠' : '🟡'}
            </div>
            <div className="p8-score-card__info">
              <div className="p8-score-card__status">Priority: {plan.priority}</div>
              <div className="p8-score-card__meta">{plan.zone} — {plan.zone_name} | {plan.incident_type}</div>
              <div className="p8-score-card__meta">Risk: {plan.risk_level} ({plan.risk_score}/100) | Workers: {plan.worker_count}</div>
            </div>
          </div>

          {/* Stats */}
          <div className="p8-stats">
            <div className="p8-stat"><span className="p8-stat__label">Priority</span><span className="p8-stat__value p8-stat__value--warn">{plan.priority}</span></div>
            <div className="p8-stat"><span className="p8-stat__label">Workers</span><span className="p8-stat__value">{plan.worker_count}</span></div>
            <div className="p8-stat"><span className="p8-stat__label">Actions</span><span className="p8-stat__value">{plan.immediate_actions.length}</span></div>
            <div className="p8-stat"><span className="p8-stat__label">PPE Items</span><span className="p8-stat__value">{plan.required_ppe.length}</span></div>
          </div>

          {/* Immediate Actions */}
          <Section title="Immediate Actions" icon="⚡" count={plan.immediate_actions.length} defaultOpen>
            {plan.immediate_actions.map((a, i) => (
              <div key={i} className="p8-item">
                <span className="p8-item__badge p8-item__badge--immediate">{a.step}</span>
                <div className="p8-item__text">
                  {a.action}
                  <span style={{display:'block',fontSize:'0.6rem',color:'#64748b'}}>{a.responsible} • {a.time_limit}</span>
                </div>
                <span className="p8-item__meta">{a.category}</span>
              </div>
            ))}
          </Section>

          {/* Evacuation */}
          <Section title="Evacuation Plan" icon="🏃" count={plan.evacuation_plan.length}>
            {plan.evacuation_plan.map((a, i) => (
              <div key={i} className="p8-item">
                <span className="p8-item__badge p8-item__badge--high">{a.step}</span>
                <div className="p8-item__text">
                  {a.action}
                  <span style={{display:'block',fontSize:'0.6rem',color:'#64748b'}}>{a.responsible} • {a.time_limit}</span>
                </div>
              </div>
            ))}
          </Section>

          {/* Isolation */}
          <Section title="Isolation Procedure" icon="🔒" count={plan.isolation_procedure.length}>
            {plan.isolation_procedure.map((a, i) => (
              <div key={i} className="p8-item">
                <span className="p8-item__badge p8-item__badge--medium">{a.step}</span>
                <div className="p8-item__text">
                  {a.action}
                  <span style={{display:'block',fontSize:'0.6rem',color:'#64748b'}}>{a.responsible} • {a.time_limit}</span>
                </div>
              </div>
            ))}
          </Section>

          {/* PPE */}
          <Section title="Required PPE" icon="🦺" count={plan.required_ppe.length}>
            <div className="p8-ppe">
              {plan.required_ppe.map((p, i) => (
                <div key={i} className="p8-ppe-item">
                  <span className="p8-ppe-item__name">{p.mandatory ? '🔴' : '🟡'} {p.item}</span>
                  <span className="p8-ppe-item__reason">{p.reason}</span>
                </div>
              ))}
            </div>
          </Section>

          {/* Medical */}
          <Section title="Medical Response" icon="🏥" count={plan.medical_response.length}>
            {plan.medical_response.map((a, i) => (
              <div key={i} className="p8-item">
                <span className="p8-item__badge p8-item__badge--critical">{a.step}</span>
                <div className="p8-item__text">{a.action}
                  <span style={{display:'block',fontSize:'0.6rem',color:'#64748b'}}>{a.responsible} • {a.time_limit}</span>
                </div>
              </div>
            ))}
          </Section>

          {/* Contacts */}
          <Section title="Emergency Contacts" icon="📞" count={plan.emergency_contacts.length}>
            {plan.emergency_contacts.map((c, i) => (
              <div key={i} className="p8-item">
                <span className="p8-item__badge p8-item__badge--low">P{c.priority}</span>
                <div className="p8-item__text"><strong>{c.role}</strong> — {c.name}</div>
                <span className="p8-item__meta">📞 {c.phone}</span>
              </div>
            ))}
          </Section>

          {/* Timeline */}
          <Section title="Incident Timeline" icon="⏱️" count={plan.incident_timeline.length}>
            {plan.incident_timeline.map((t, i) => (
              <div key={i} className="p8-timeline-item">
                <span className="p8-timeline-item__time">{t.time}</span>
                <span className="p8-timeline-item__event">{t.event}</span>
              </div>
            ))}
          </Section>

          {/* Recovery */}
          <Section title="Recovery Checklist" icon="✅">
            {plan.recovery_checklist.map((cat, i) => (
              <div key={i}>
                <div className="p8-checklist-cat">{cat.category}</div>
                {cat.items.map((item, j) => (
                  <div key={j} className="p8-checklist-item">
                    <span className="p8-checklist-item__dot" />
                    <span>{item.item}</span>
                    <span className="p8-item__meta">{item.priority}</span>
                  </div>
                ))}
              </div>
            ))}
          </Section>
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

export default EmergencyPage;
