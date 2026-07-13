import { useState } from "react";
import { runAgentAnalysis } from "../services/api";
import "../AgentAnalysis.css";

const ZONES = ["Zone A", "Zone B", "Zone C", "Zone D"];

const STATUS_ICONS = {
  completed: "✅",
  failed: "❌",
  running: "⏳",
  pending: "⬜",
  skipped: "⏭️",
};

function AgentAnalysis() {
  const [zone, setZone] = useState("Zone A");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = () => {
    setLoading(true);
    setError(null);
    setResult(null);
    runAgentAnalysis(zone)
      .then(setResult)
      .catch((err) =>
        setError(err.response?.data?.detail || "Agent analysis failed")
      )
      .finally(() => setLoading(false));
  };

  // Get agent result by name
  const getAgent = (name) =>
    result?.results?.find((r) => r.agent_name === name);

  return (
    <main className="agent-page">
      <header className="agent-page__header">
        <div className="agent-page__logo">🤖</div>
        <h1 className="agent-page__title">Multi-Agent Analysis</h1>
        <p className="agent-page__subtitle">Agentic AI Orchestrator</p>
      </header>

      {/* Controls */}
      <div className="agent-page__controls">
        <select
          value={zone}
          onChange={(e) => setZone(e.target.value)}
          className="agent-select"
        >
          {ZONES.map((z) => (
            <option key={z} value={z}>{z}</option>
          ))}
        </select>
        <button
          className="agent-btn agent-btn--run"
          onClick={handleAnalyze}
          disabled={loading}
        >
          {loading ? "Running Agents..." : "Run Agent Analysis"}
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="agent-page__state">
          <div className="agent-spinner" />
          <p>Executing agent pipeline...</p>
          <p className="agent-page__state-hint">Risk → Incident → Knowledge Graph → Compliance → Emergency</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="agent-page__state agent-page__state--error">
          <p>{error}</p>
        </div>
      )}

      {/* Results */}
      {!loading && result && (
        <div className="agent-page__results">
          {/* Summary header */}
          <div className="agent-summary-card">
            <div className="agent-summary-card__header">
              <h3>{result.zone} — {result.zone_name}</h3>
              <div className="agent-summary-card__stats">
                <span className="agent-pill agent-pill--ok">{result.agents_completed} completed</span>
                {result.agents_failed > 0 && (
                  <span className="agent-pill agent-pill--err">{result.agents_failed} failed</span>
                )}
                <span className="agent-pill">{result.total_duration_ms.toFixed(0)}ms</span>
              </div>
            </div>
          </div>

          {/* Pipeline */}
          <div className="agent-pipeline">
            <h3 className="agent-section-title">Agent Pipeline</h3>
            <div className="agent-pipeline__steps">
              {result.pipeline.map((step, i) => (
                <div key={i} className="agent-pipeline__step">
                  <span className="agent-pipeline__icon">{step.icon}</span>
                  <span className="agent-pipeline__name">{step.display_name}</span>
                  <span className="agent-pipeline__status">{STATUS_ICONS[step.status]}</span>
                  <span className="agent-pipeline__time">{step.duration_ms.toFixed(0)}ms</span>
                  {i < result.pipeline.length - 1 && (
                    <span className="agent-pipeline__arrow">→</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Overall Summary */}
          {result.overall_summary && (
            <AgentSection title="Overall Summary" icon="🧠" defaultOpen>
              <div className="agent-summary-text">{result.overall_summary}</div>
            </AgentSection>
          )}

          {/* Risk Agent */}
          {getAgent("risk_agent")?.status === "completed" && (
            <AgentSection title="Risk Assessment" icon="🔥" agent={getAgent("risk_agent")}>
              {(() => {
                const d = getAgent("risk_agent").data;
                return (
                  <>
                    <div className="agent-risk-header">
                      <span className={`agent-badge agent-badge--${d.risk_level?.toLowerCase()}`}>
                        {d.risk_level}
                      </span>
                      <span className="agent-risk-score">{d.risk_score}/100</span>
                      <span className="agent-risk-hazard">{d.hazard_level}</span>
                    </div>
                    {d.compound_risks?.length > 0 && (
                      <div className="agent-list">
                        <h4>Compound Risks</h4>
                        {d.compound_risks.map((r, i) => (
                          <div key={i} className="agent-list-item">
                            <span className={`agent-severity agent-severity--${r.severity?.toLowerCase()}`}>{r.severity}</span>
                            <span>{r.name}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {d.recommendations?.length > 0 && (
                      <div className="agent-list">
                        <h4>Recommendations</h4>
                        {d.recommendations.map((r, i) => (
                          <div key={i} className="agent-list-item">
                            <span className={`agent-severity agent-severity--${r.priority?.toLowerCase()}`}>{r.priority}</span>
                            <span>{r.action}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                );
              })()}
            </AgentSection>
          )}

          {/* Incident Agent */}
          {getAgent("incident_agent")?.status === "completed" && (
            <AgentSection title="Incident Intelligence" icon="📚" agent={getAgent("incident_agent")}>
              {(() => {
                const d = getAgent("incident_agent").data;
                return (
                  <>
                    <div className="agent-stats-row">
                      <StatCard label="Similar Incidents" value={d.similar_incidents?.length || 0} />
                      <StatCard label="Lessons Learned" value={d.lessons_learned?.length || 0} />
                      <StatCard label="Regulations" value={d.related_regulations?.length || 0} />
                      <StatCard label="Documents Retrieved" value={d.retrieval_count || 0} />
                    </div>
                    {d.similar_incidents?.length > 0 && (
                      <div className="agent-list">
                        <h4>Similar Incidents</h4>
                        {d.similar_incidents.map((inc, i) => (
                          <div key={i} className="agent-list-item">
                            <span className="agent-list-item__title">{inc.title}</span>
                            <span className="agent-list-item__meta">{inc.document_type} • {(inc.relevance * 100).toFixed(0)}%</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                );
              })()}
            </AgentSection>
          )}

          {/* KG Agent */}
          {getAgent("knowledge_graph_agent")?.status === "completed" && (
            <AgentSection title="Knowledge Graph Insights" icon="🕸️" agent={getAgent("knowledge_graph_agent")}>
              {(() => {
                const d = getAgent("knowledge_graph_agent").data;
                if (!d.available) return <p className="agent-muted">{d.reason}</p>;
                return (
                  <>
                    <div className="agent-stats-row">
                      <StatCard label="Nodes" value={d.total_nodes || 0} />
                      <StatCard label="Edges" value={d.total_edges || 0} />
                      <StatCard label="Equipment" value={d.connected_equipment?.length || 0} />
                      <StatCard label="Workers" value={d.connected_workers?.length || 0} />
                    </div>
                    {d.hazards?.length > 0 && (
                      <div className="agent-list">
                        <h4>Known Hazards</h4>
                        {d.hazards.map((h, i) => (
                          <div key={i} className="agent-list-item">☢️ {h.name}</div>
                        ))}
                      </div>
                    )}
                  </>
                );
              })()}
            </AgentSection>
          )}

          {/* Compliance Agent */}
          {getAgent("compliance_agent")?.status === "completed" && (
            <AgentSection title="Compliance Analysis" icon="📋" agent={getAgent("compliance_agent")}>
              {(() => {
                const d = getAgent("compliance_agent").data;
                return (
                  <>
                    <div className="agent-stats-row">
                      <StatCard label="Compliance Gaps" value={d.total_gaps || 0} warn={d.total_gaps > 0} />
                      <StatCard label="Required Actions" value={d.required_actions?.length || 0} />
                      <StatCard label="Regulations Found" value={d.regulations?.length || 0} />
                    </div>
                    {d.compliance_gaps?.length > 0 && (
                      <div className="agent-list">
                        <h4>Compliance Gaps</h4>
                        {d.compliance_gaps.map((g, i) => (
                          <div key={i} className="agent-list-item">
                            <span className={`agent-severity agent-severity--${g.severity?.toLowerCase()}`}>{g.severity}</span>
                            <span>{g.description}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {d.required_actions?.length > 0 && (
                      <div className="agent-list">
                        <h4>Required Actions</h4>
                        {d.required_actions.map((a, i) => (
                          <div key={i} className="agent-list-item">
                            <span className={`agent-severity agent-severity--${a.priority?.toLowerCase()}`}>{a.priority}</span>
                            <span>{a.action}</span>
                            <span className="agent-list-item__meta">{a.regulation}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                );
              })()}
            </AgentSection>
          )}

          {/* Emergency Agent */}
          {getAgent("emergency_response_agent")?.status === "completed" && (
            <AgentSection title="Emergency Response" icon="🚨" agent={getAgent("emergency_response_agent")}>
              {(() => {
                const d = getAgent("emergency_response_agent").data;
                return (
                  <>
                    <div className="agent-emergency-header">
                      <span className={`agent-badge agent-badge--${d.priority?.toLowerCase()}`}>
                        Priority: {d.priority}
                      </span>
                      <span>Workers: {d.worker_count}</span>
                    </div>
                    {d.evacuation_steps?.length > 0 && (
                      <div className="agent-evac-steps">
                        <h4>Evacuation Steps</h4>
                        {d.evacuation_steps.map((s, i) => (
                          <div key={i} className="agent-evac-step">
                            <span className="agent-evac-step__num">{s.step}</span>
                            <div className="agent-evac-step__body">
                              <span className="agent-evac-step__action">{s.action}</span>
                              <span className="agent-evac-step__meta">
                                {s.responsible} • {s.time_limit}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    {d.emergency_contacts?.length > 0 && (
                      <div className="agent-list">
                        <h4>Emergency Contacts</h4>
                        {d.emergency_contacts.map((c, i) => (
                          <div key={i} className="agent-list-item">
                            <span className="agent-list-item__title">{c.role}</span>
                            <span>{c.name}</span>
                            <span className="agent-list-item__meta">📞 {c.phone}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                );
              })()}
            </AgentSection>
          )}

          {/* Failed Agents */}
          {result.results.filter((r) => r.status === "failed").map((r, i) => (
            <div key={i} className="agent-failed">
              <span>❌ {r.agent_type} failed: {r.error}</span>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}

/* ── Helpers ── */

function AgentSection({ title, icon, agent, defaultOpen, children }) {
  const [open, setOpen] = useState(defaultOpen || false);
  return (
    <section className="agent-section">
      <button className="agent-section__header" onClick={() => setOpen(!open)}>
        <span className="agent-section__icon">{icon}</span>
        <span className="agent-section__title">{title}</span>
        {agent && (
          <span className="agent-section__time">{agent.duration_ms?.toFixed(0)}ms</span>
        )}
        <span className="agent-section__chevron">{open ? "▼" : "▶"}</span>
      </button>
      {open && <div className="agent-section__body">{children}</div>}
    </section>
  );
}

function StatCard({ label, value, warn }) {
  return (
    <div className="agent-stat-card">
      <span className="agent-stat-card__label">{label}</span>
      <span className={`agent-stat-card__value ${warn ? "agent-stat-card__value--warn" : ""}`}>
        {value}
      </span>
    </div>
  );
}

export default AgentAnalysis;
