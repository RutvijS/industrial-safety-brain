import { useState } from "react";
import RiskScoreCard from "../components/RiskScoreCard";
import { runRiskAnalysis } from "../services/api";
import "../RiskAnalysis.css";

function RiskAnalysis() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = () => {
    setLoading(true);
    setError(null);
    runRiskAnalysis()
      .then(setResult)
      .catch((err) => setError(err.response?.data?.detail || "Risk analysis failed"))
      .finally(() => setLoading(false));
  };

  return (
    <main className="risk-analysis">
      <header className="risk-analysis__header">
        <div className="risk-analysis__logo">🔥</div>
        <h1 className="risk-analysis__title">Risk Analysis</h1>
        <p className="risk-analysis__subtitle">Compound Risk Detection Engine</p>
      </header>

      {/* Run Analysis Button */}
      <button
        className="risk-analysis__run-btn"
        onClick={handleAnalyze}
        disabled={loading}
      >
        {loading ? "Analyzing..." : "Run Risk Analysis"}
      </button>

      {/* Loading */}
      {loading && (
        <div className="risk-analysis__state">
          <div className="risk-analysis__spinner" />
          <p>Analyzing plant state and generating assessment...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="risk-analysis__state risk-analysis__state--error">
          <p>{error}</p>
        </div>
      )}

      {/* Results */}
      {!loading && !error && result && (
        <div className="risk-analysis__results">
          {/* Overall Summary */}
          <div className="risk-analysis__overall">
            <RiskScoreCard
              score={result.overall_risk_score}
              riskLevel={result.overall_risk}
              confidence={result.overall_confidence}
              hazard={result.overall_risk === "CRITICAL" ? "Very High" : result.overall_risk === "HIGH" ? "High" : "Moderate"}
            />
            <div className="risk-analysis__summary-stats">
              <div className="risk-analysis__stat">
                <span className="risk-analysis__stat-value">{result.zone_assessments.length}</span>
                <span className="risk-analysis__stat-label">Zones Analyzed</span>
              </div>
              <div className="risk-analysis__stat">
                <span className="risk-analysis__stat-value risk-analysis__stat-value--warn">
                  {result.total_compound_risks}
                </span>
                <span className="risk-analysis__stat-label">Compound Risks</span>
              </div>
              <div className="risk-analysis__stat">
                <span className="risk-analysis__stat-value">{result.total_recommendations}</span>
                <span className="risk-analysis__stat-label">Recommendations</span>
              </div>
            </div>
          </div>

          {/* Per-Zone Assessments */}
          {result.zone_assessments.map((zone) => (
            <ZoneAssessmentCard key={zone.zone} data={zone} />
          ))}
        </div>
      )}

      {!loading && !error && !result && (
        <div className="risk-analysis__state">
          <p>Click "Run Risk Analysis" to analyze the current plant state</p>
        </div>
      )}
    </main>
  );
}

/* ── Zone Assessment Card ────────────────────────────── */

function ZoneAssessmentCard({ data }) {
  const [expanded, setExpanded] = useState(false);

  const levelClass =
    data.overall_risk === "CRITICAL" ? "zone-risk--critical" :
    data.overall_risk === "HIGH" ? "zone-risk--high" :
    data.overall_risk === "MEDIUM" ? "zone-risk--medium" :
    "zone-risk--low";

  return (
    <div className={`zone-risk-card ${levelClass}`}>
      {/* Card Header */}
      <button
        className="zone-risk-card__header"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <div className="zone-risk-card__header-left">
          <h3 className="zone-risk-card__zone">{data.zone}</h3>
          <span className="zone-risk-card__name">{data.zone_name}</span>
        </div>
        <div className="zone-risk-card__header-right">
          <span className={`zone-risk-card__badge ${levelClass}`}>{data.overall_risk}</span>
          <span className="zone-risk-card__score">{data.risk_score}/100</span>
        </div>
        <span className={`zone-risk-card__chevron ${expanded ? "zone-risk-card__chevron--open" : ""}`}>
          &#9660;
        </span>
      </button>

      {expanded && (
        <div className="zone-risk-card__body">
          {/* Risk Factors */}
          <section className="zone-risk-card__section">
            <h4>Risk Factors</h4>
            <div className="zone-risk-card__factors">
              {data.risk_factors.map((f) => (
                <div key={f.name} className="risk-factor">
                  <span className="risk-factor__name">{f.name.replace(/_/g, " ")}</span>
                  <div className="risk-factor__bar-bg">
                    <div
                      className={`risk-factor__bar ${
                        f.status === "Critical" ? "risk-factor__bar--critical" :
                        f.status === "Warning" ? "risk-factor__bar--warning" :
                        "risk-factor__bar--normal"
                      }`}
                      style={{ width: `${Math.min(f.normalized_score, 100)}%` }}
                    />
                  </div>
                  <span className="risk-factor__value">{f.normalized_score}</span>
                </div>
              ))}
            </div>
          </section>

          {/* Detected Compound Risks */}
          {data.detected_compound_risks.length > 0 && (
            <section className="zone-risk-card__section">
              <h4>Detected Compound Risks</h4>
              <ul className="zone-risk-card__list">
                {data.detected_compound_risks.map((r, idx) => (
                  <li key={idx} className="compound-risk-item">
                    <div className="compound-risk-item__header">
                      <span className={`badge ${
                        r.severity === "Critical" ? "badge--critical" :
                        r.severity === "High" ? "badge--warning" :
                        "badge--muted"
                      }`}>{r.severity}</span>
                      <span className="compound-risk-item__name">{r.name}</span>
                    </div>
                    <p className="compound-risk-item__desc">{r.description}</p>
                    {r.evidence.length > 0 && (
                      <ul className="compound-risk-item__evidence">
                        {r.evidence.map((e, i) => (
                          <li key={i}>{e.detail}</li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Supporting Evidence */}
          {data.supporting_evidence.length > 0 && (
            <section className="zone-risk-card__section">
              <h4>Supporting Evidence</h4>
              <ul className="zone-risk-card__evidence-list">
                {data.supporting_evidence.map((e, idx) => (
                  <li key={idx} className="evidence-item">
                    <span className="evidence-item__source">[{e.source}]</span>
                    <span className="evidence-item__detail">{e.detail}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Recommended Actions */}
          {data.recommended_actions.length > 0 && (
            <section className="zone-risk-card__section">
              <h4>Recommended Actions</h4>
              <ul className="zone-risk-card__list">
                {data.recommended_actions.map((r, idx) => (
                  <li key={idx} className="recommendation-item">
                    <span className={`recommendation-item__priority ${
                      r.priority === "IMMEDIATE" ? "priority--immediate" :
                      r.priority === "HIGH" ? "priority--high" :
                      "priority--medium"
                    }`}>{r.priority}</span>
                    <span className="recommendation-item__action">{r.action}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Reasoning */}
          {data.reasoning.length > 0 && (
            <section className="zone-risk-card__section">
              <h4>Reasoning Chain</h4>
              <ol className="zone-risk-card__reasoning">
                {data.reasoning.map((r, idx) => (
                  <li key={idx}>{r}</li>
                ))}
              </ol>
            </section>
          )}

          {/* Gemini Explanation */}
          {data.gemini_explanation && (
            <section className="zone-risk-card__section zone-risk-card__section--explanation">
              <h4>AI Explanation</h4>
              <div className="zone-risk-card__explanation">
                {data.gemini_explanation}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}

export default RiskAnalysis;
