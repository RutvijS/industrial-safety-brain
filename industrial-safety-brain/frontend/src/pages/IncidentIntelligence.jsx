import { useState } from "react";
import {
  runIncidentIntelligence,
  ingestDocuments,
  getDocuments,
} from "../services/api";
import "../IncidentIntelligence.css";

const ZONES = ["Zone A", "Zone B", "Zone C", "Zone D"];

const DOC_TYPES = [
  "Incident Report",
  "Near Miss",
  "SOP",
  "OISD Guideline",
  "Factory Act",
  "DGMS Guideline",
  "Maintenance Manual",
  "Emergency Procedure",
  "General",
];

function IncidentIntelligence() {
  const [zone, setZone] = useState("Zone A");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Upload state
  const [files, setFiles] = useState([]);
  const [docType, setDocType] = useState("General");
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [docList, setDocList] = useState([]);

  const handleAnalyze = () => {
    setLoading(true);
    setError(null);
    runIncidentIntelligence(zone)
      .then(setResult)
      .catch((err) =>
        setError(err.response?.data?.detail || "Analysis failed")
      )
      .finally(() => setLoading(false));
  };

  const handleUpload = () => {
    if (files.length === 0) return;
    setUploading(true);
    setUploadResult(null);
    ingestDocuments(Array.from(files), docType)
      .then((res) => {
        setUploadResult(res);
        setFiles([]);
        loadDocs();
      })
      .catch((err) =>
        setError(err.response?.data?.detail || "Upload failed")
      )
      .finally(() => setUploading(false));
  };

  const loadDocs = () => {
    getDocuments().then(setDocList).catch(() => {});
  };

  return (
    <main className="incident-intel">
      <header className="incident-intel__header">
        <div className="incident-intel__logo">📚</div>
        <h1 className="incident-intel__title">Incident Intelligence</h1>
        <p className="incident-intel__subtitle">
          RAG-Powered Evidence Analysis
        </p>
      </header>

      {/* ── Document Upload Section ── */}
      <section className="incident-intel__upload-section">
        <h2 className="incident-intel__section-title">Ingest Documents</h2>
        <div className="incident-intel__upload-row">
          <input
            type="file"
            multiple
            accept=".pdf,.txt,.md"
            onChange={(e) => setFiles(e.target.files)}
            className="incident-intel__file-input"
          />
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="incident-intel__select"
          >
            {DOC_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <button
            className="incident-intel__btn incident-intel__btn--upload"
            onClick={handleUpload}
            disabled={uploading || files.length === 0}
          >
            {uploading ? "Uploading..." : "Upload & Ingest"}
          </button>
          <button
            className="incident-intel__btn incident-intel__btn--secondary"
            onClick={loadDocs}
          >
            View Indexed
          </button>
        </div>

        {uploadResult && (
          <div className="incident-intel__upload-result">
            ✅ {uploadResult.documents_processed} document(s) processed,{" "}
            {uploadResult.chunks_created} chunks created
          </div>
        )}

        {docList.length > 0 && (
          <div className="incident-intel__doc-list">
            <h3>Indexed Documents ({docList.length})</h3>
            <ul>
              {docList.map((d, i) => (
                <li key={i}>
                  <span className="doc-list__name">{d.source_filename}</span>
                  <span className="doc-list__type">{d.document_type}</span>
                  <span className="doc-list__chunks">{d.chunk_count} chunks</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {/* ── Analysis Section ── */}
      <section className="incident-intel__analysis-section">
        <h2 className="incident-intel__section-title">Run Analysis</h2>
        <div className="incident-intel__controls">
          <select
            value={zone}
            onChange={(e) => setZone(e.target.value)}
            className="incident-intel__select"
          >
            {ZONES.map((z) => (
              <option key={z} value={z}>{z}</option>
            ))}
          </select>
          <button
            className="incident-intel__btn incident-intel__btn--analyze"
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? "Analyzing..." : "Run Incident Intelligence"}
          </button>
        </div>
      </section>

      {/* Loading */}
      {loading && (
        <div className="incident-intel__state">
          <div className="incident-intel__spinner" />
          <p>Retrieving evidence and generating analysis...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="incident-intel__state incident-intel__state--error">
          <p>{error}</p>
        </div>
      )}

      {/* Results */}
      {!loading && !error && result && (
        <div className="incident-intel__results">
          {/* Summary Header */}
          <div className="intel-summary-card">
            <div className="intel-summary-card__header">
              <h3>{result.zone} — {result.zone_name}</h3>
              <span className={`intel-badge intel-badge--${result.risk_level.toLowerCase()}`}>
                {result.risk_level}
              </span>
            </div>
            <div className="intel-summary-card__stats">
              <span>Score: {result.risk_score}/100</span>
              <span>Documents Retrieved: {result.retrieval_count}</span>
              <span>Citations: {result.citations.length}</span>
            </div>
          </div>

          {/* Similar Incidents */}
          {result.similar_incidents.length > 0 && (
            <ResultSection title="Similar Incidents" icon="🔍">
              {result.similar_incidents.map((doc, i) => (
                <DocCard key={i} doc={doc} />
              ))}
            </ResultSection>
          )}

          {/* Lessons Learned */}
          {result.lessons_learned.length > 0 && (
            <ResultSection title="Lessons Learned" icon="💡">
              {result.lessons_learned.map((l, i) => (
                <div key={i} className="lesson-card">
                  <p className="lesson-card__text">{l.lesson}</p>
                  <span className="lesson-card__source">
                    Source: {l.source}
                  </span>
                </div>
              ))}
            </ResultSection>
          )}

          {/* Regulations */}
          {result.related_regulations.length > 0 && (
            <ResultSection title="Related Regulations" icon="📖">
              {result.related_regulations.map((doc, i) => (
                <DocCard key={i} doc={doc} />
              ))}
            </ResultSection>
          )}

          {/* Supporting Documents */}
          {result.supporting_documents.length > 0 && (
            <ResultSection title="Supporting Documents" icon="📄">
              {result.supporting_documents.map((doc, i) => (
                <DocCard key={i} doc={doc} />
              ))}
            </ResultSection>
          )}

          {/* Citations */}
          {result.citations.length > 0 && (
            <ResultSection title="Citations" icon="📌">
              <ol className="citation-list">
                {result.citations.map((c, i) => (
                  <li key={i} className="citation-item">
                    <strong>{c.source}</strong>
                    <span className="citation-item__meta">
                      ({c.document_type}, Page {c.page}, {c.section})
                    </span>
                    <p className="citation-item__excerpt">"{c.excerpt}"</p>
                  </li>
                ))}
              </ol>
            </ResultSection>
          )}

          {/* LLM Explanation */}
          {result.llm_explanation && (
            <ResultSection title="AI Explanation" icon="🤖">
              <div className="intel-explanation">
                {result.llm_explanation}
              </div>
            </ResultSection>
          )}

          {/* Empty state */}
          {result.retrieval_count === 0 && !result.llm_explanation && (
            <div className="incident-intel__state">
              <p>No documents indexed yet. Upload documents above to enable evidence-based analysis.</p>
            </div>
          )}
        </div>
      )}
    </main>
  );
}

/* ── Helpers ── */

function ResultSection({ title, icon, children }) {
  return (
    <section className="intel-section">
      <h3 className="intel-section__title">
        <span>{icon}</span> {title}
      </h3>
      <div className="intel-section__body">{children}</div>
    </section>
  );
}

function DocCard({ doc }) {
  return (
    <div className="doc-card">
      <div className="doc-card__header">
        <span className="doc-card__title">{doc.title || doc.source_filename}</span>
        <span className="doc-card__type">{doc.document_type}</span>
        <span className="doc-card__relevance">
          {(doc.relevance_score * 100).toFixed(0)}%
        </span>
      </div>
      <p className="doc-card__content">{doc.content.slice(0, 300)}...</p>
      <div className="doc-card__meta">
        <span>Page {doc.page_number}</span>
        <span>{doc.section}</span>
      </div>
    </div>
  );
}

export default IncidentIntelligence;
