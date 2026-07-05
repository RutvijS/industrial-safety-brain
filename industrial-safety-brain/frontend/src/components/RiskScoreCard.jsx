/**
 * RiskScoreCard — Displays the overall risk score with a visual gauge.
 *
 * Props:
 *   score      - 0-100 risk score
 *   riskLevel  - CRITICAL / HIGH / MEDIUM / LOW
 *   confidence - 0-99 confidence percentage
 *   hazard     - Very High / High / Moderate / Low / Very Low
 */

function RiskScoreCard({ score, riskLevel, confidence, hazard }) {
  const levelClass =
    riskLevel === "CRITICAL" ? "risk-score--critical" :
    riskLevel === "HIGH" ? "risk-score--high" :
    riskLevel === "MEDIUM" ? "risk-score--medium" :
    "risk-score--low";

  return (
    <div className={`risk-score-card ${levelClass}`}>
      <div className="risk-score-card__gauge">
        <div className="risk-score-card__score">{score}</div>
        <div className="risk-score-card__label">/ 100</div>
      </div>
      <div className="risk-score-card__details">
        <div className="risk-score-card__level">{riskLevel}</div>
        <div className="risk-score-card__meta">
          <span>Hazard: {hazard}</span>
          <span>Confidence: {confidence}%</span>
        </div>
      </div>
    </div>
  );
}

export default RiskScoreCard;
