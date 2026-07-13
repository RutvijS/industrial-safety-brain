import { useState, useEffect, useRef, useCallback } from "react";
import {
  buildKnowledgeGraph,
  getGraphStatus,
  getZoneGraph,
  getEquipmentGraph,
  getIncidentGraph,
  searchGraph,
} from "../services/api";
import "../KnowledgeGraph.css";

/* ── Node color mapping ── */
const NODE_COLORS = {
  Zone: "#3b82f6",
  Equipment: "#f97316",
  Sensor: "#22c55e",
  Permit: "#eab308",
  Maintenance: "#8b5cf6",
  Incident: "#ef4444",
  Worker: "#06b6d4",
  Supervisor: "#ec4899",
  Shift: "#64748b",
  Hazard: "#dc2626",
  Regulation: "#14b8a6",
};

const NODE_ICONS = {
  Zone: "🏭", Equipment: "⚙️", Sensor: "📡", Permit: "📋",
  Maintenance: "🔧", Incident: "⚠️", Worker: "👷", Supervisor: "👤",
  Shift: "🕐", Hazard: "☢️", Regulation: "📖",
};

const QUERY_TYPES = [
  { id: "zone", label: "Zone", options: ["Zone A", "Zone B", "Zone C", "Zone D"] },
];

function KnowledgeGraph() {
  const [status, setStatus] = useState(null);
  const [graph, setGraph] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [building, setBuilding] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [buildResult, setBuildResult] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [activeView, setActiveView] = useState("zone");
  const [activeZone, setActiveZone] = useState("Zone A");
  const svgRef = useRef(null);

  // Fetch status on mount
  useEffect(() => {
    getGraphStatus().then(setStatus).catch(() => {});
  }, []);

  const handleBuild = () => {
    setBuilding(true);
    setError(null);
    setBuildResult(null);
    buildKnowledgeGraph()
      .then((res) => {
        setBuildResult(res);
        getGraphStatus().then(setStatus);
      })
      .catch((err) => setError(err.response?.data?.detail || "Build failed"))
      .finally(() => setBuilding(false));
  };

  const handleLoadZone = (zone) => {
    setActiveZone(zone);
    setActiveView("zone");
    setLoading(true);
    setSelectedNode(null);
    getZoneGraph(zone)
      .then((res) => { setGraph(res.graph); setLoading(false); })
      .catch(() => { setError("Failed to load zone graph"); setLoading(false); });
  };

  const handleLoadEquipment = (eq) => {
    setActiveView("equipment");
    setLoading(true);
    setSelectedNode(null);
    getEquipmentGraph(eq)
      .then((res) => { setGraph(res.graph); setLoading(false); })
      .catch(() => { setError("Failed to load equipment graph"); setLoading(false); });
  };

  const handleLoadIncident = (inc) => {
    setActiveView("incident");
    setLoading(true);
    setSelectedNode(null);
    getIncidentGraph(inc)
      .then((res) => { setGraph(res.graph); setLoading(false); })
      .catch(() => { setError("Failed to load incident graph"); setLoading(false); });
  };

  const handleSearch = () => {
    if (!searchQuery.trim()) return;
    searchGraph(searchQuery)
      .then(setSearchResults)
      .catch(() => setSearchResults([]));
  };

  const handleNodeClick = (node) => {
    setSelectedNode(node);
    // If it's an equipment or incident, load its graph
    if (node.node_type === "Equipment") handleLoadEquipment(node.id);
    else if (node.node_type === "Incident") handleLoadIncident(node.id);
  };

  // Simple force-directed layout positions
  const layoutNodes = useCallback(() => {
    if (!graph || !graph.nodes.length) return [];
    const cx = 400, cy = 300;
    const nodes = graph.nodes;
    const n = nodes.length;

    return nodes.map((node, i) => {
      const isCenter = node.id === graph.center_node;
      const angle = (2 * Math.PI * i) / n;
      const radius = isCenter ? 0 : 120 + Math.min(n * 8, 200);
      return {
        ...node,
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
        color: NODE_COLORS[node.node_type] || "#64748b",
        icon: NODE_ICONS[node.node_type] || "●",
      };
    });
  }, [graph]);

  const positioned = layoutNodes();

  return (
    <main className="kg-page">
      <header className="kg-page__header">
        <div className="kg-page__logo">🕸️</div>
        <h1 className="kg-page__title">Knowledge Graph</h1>
        <p className="kg-page__subtitle">Industrial Relationship Intelligence</p>
      </header>

      {/* Status + Build Bar */}
      <div className="kg-page__toolbar">
        <button
          className="kg-btn kg-btn--build"
          onClick={handleBuild}
          disabled={building}
        >
          {building ? "Building..." : "Build Graph"}
        </button>

        {status && (
          <div className="kg-status-pills">
            <span className={`kg-pill ${status.connected ? "kg-pill--ok" : "kg-pill--err"}`}>
              {status.connected ? "Connected" : "Disconnected"}
            </span>
            <span className="kg-pill">{status.node_count} nodes</span>
            <span className="kg-pill">{status.relationship_count} edges</span>
          </div>
        )}

        {buildResult && (
          <span className="kg-build-result">
            ✅ {buildResult.nodes_created} nodes, {buildResult.relationships_created} relationships ({buildResult.duration_seconds}s)
          </span>
        )}
      </div>

      {error && (
        <div className="kg-page__error">
          <p>{error}</p>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      <div className="kg-page__content">
        {/* Left Panel: Navigation */}
        <aside className="kg-nav">
          {/* Zone Explorer */}
          <div className="kg-nav__section">
            <h3 className="kg-nav__title">Zone Explorer</h3>
            {["Zone A", "Zone B", "Zone C", "Zone D"].map((z) => (
              <button
                key={z}
                className={`kg-nav__btn ${activeZone === z && activeView === "zone" ? "kg-nav__btn--active" : ""}`}
                onClick={() => handleLoadZone(z)}
              >
                🏭 {z}
              </button>
            ))}
          </div>

          {/* Search */}
          <div className="kg-nav__section">
            <h3 className="kg-nav__title">Search</h3>
            <div className="kg-search">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Equipment, Incident..."
                className="kg-search__input"
              />
              <button className="kg-search__btn" onClick={handleSearch}>🔍</button>
            </div>
            {searchResults.length > 0 && (
              <div className="kg-search-results">
                {searchResults.map((n, i) => (
                  <button
                    key={i}
                    className="kg-search-result"
                    onClick={() => handleNodeClick(n)}
                  >
                    <span className="kg-search-result__icon">{NODE_ICONS[n.node_type] || "●"}</span>
                    <span className="kg-search-result__label">{n.label}</span>
                    <span className="kg-search-result__type">{n.node_type}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Node Type Legend */}
          <div className="kg-nav__section">
            <h3 className="kg-nav__title">Legend</h3>
            <div className="kg-legend">
              {Object.entries(NODE_COLORS).map(([type, color]) => (
                <div key={type} className="kg-legend__item">
                  <span className="kg-legend__dot" style={{ background: color }} />
                  <span>{NODE_ICONS[type]} {type}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Graph Stats */}
          {status && status.connected && Object.keys(status.node_types).length > 0 && (
            <div className="kg-nav__section">
              <h3 className="kg-nav__title">Node Types</h3>
              {Object.entries(status.node_types).map(([type, count]) => (
                <div key={type} className="kg-stat-row">
                  <span>{type}</span>
                  <span className="kg-stat-row__count">{count}</span>
                </div>
              ))}
            </div>
          )}
        </aside>

        {/* Center: Graph Visualization */}
        <div className="kg-graph-container">
          {loading && (
            <div className="kg-graph-state">
              <div className="kg-spinner" />
              <p>Loading graph...</p>
            </div>
          )}

          {!loading && !graph && (
            <div className="kg-graph-state">
              <p>Select a zone or search for entities to visualize the graph.</p>
              <p className="kg-graph-state__hint">Build the graph first if you haven't already.</p>
            </div>
          )}

          {!loading && graph && positioned.length > 0 && (
            <svg
              ref={svgRef}
              className="kg-svg"
              viewBox="0 0 800 600"
              preserveAspectRatio="xMidYMid meet"
            >
              <defs>
                <marker id="arrow" viewBox="0 0 10 10" refX="20" refY="5"
                  markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(148,163,184,0.4)" />
                </marker>
              </defs>

              {/* Edges */}
              {graph.edges.map((edge, i) => {
                const src = positioned.find((n) => n.id === edge.source);
                const tgt = positioned.find((n) => n.id === edge.target);
                if (!src || !tgt) return null;
                const mx = (src.x + tgt.x) / 2;
                const my = (src.y + tgt.y) / 2;
                return (
                  <g key={`e-${i}`}>
                    <line
                      x1={src.x} y1={src.y} x2={tgt.x} y2={tgt.y}
                      className="kg-edge"
                      markerEnd="url(#arrow)"
                    />
                    <text x={mx} y={my - 4} className="kg-edge-label">
                      {edge.relationship}
                    </text>
                  </g>
                );
              })}

              {/* Nodes */}
              {positioned.map((node) => {
                const isSelected = selectedNode?.id === node.id;
                return (
                  <g
                    key={node.id}
                    className="kg-node"
                    onClick={() => setSelectedNode(node)}
                  >
                    <circle
                      cx={node.x} cy={node.y} r={isSelected ? 22 : 18}
                      fill={node.color}
                      fillOpacity={0.2}
                      stroke={node.color}
                      strokeWidth={isSelected ? 2.5 : 1.5}
                    />
                    <text x={node.x} y={node.y + 4} textAnchor="middle" className="kg-node-icon">
                      {node.icon}
                    </text>
                    <text x={node.x} y={node.y + 32} textAnchor="middle" className="kg-node-label">
                      {node.label.length > 15 ? node.label.slice(0, 15) + "…" : node.label}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}

          {!loading && graph && positioned.length === 0 && (
            <div className="kg-graph-state">
              <p>No nodes found for this query.</p>
            </div>
          )}

          {/* Graph info bar */}
          {graph && (
            <div className="kg-graph-info">
              <span>{graph.node_count} nodes</span>
              <span>{graph.edge_count} edges</span>
              {graph.center_node && <span>Center: {graph.center_node}</span>}
            </div>
          )}
        </div>

        {/* Right Panel: Node Details */}
        {selectedNode && (
          <aside className="kg-details">
            <button className="kg-details__close" onClick={() => setSelectedNode(null)}>✕</button>
            <h3 className="kg-details__title">
              {NODE_ICONS[selectedNode.node_type]} {selectedNode.label}
            </h3>
            <span className="kg-details__type" style={{ color: NODE_COLORS[selectedNode.node_type] }}>
              {selectedNode.node_type}
            </span>

            <div className="kg-details__props">
              {Object.entries(selectedNode.properties || {}).map(([key, val]) => (
                <div key={key} className="kg-prop">
                  <span className="kg-prop__key">{key.replace(/_/g, " ")}</span>
                  <span className="kg-prop__val">{String(val)}</span>
                </div>
              ))}
            </div>

            {/* Quick actions */}
            <div className="kg-details__actions">
              {selectedNode.node_type === "Equipment" && (
                <button className="kg-btn kg-btn--sm" onClick={() => handleLoadEquipment(selectedNode.id)}>
                  View Equipment Graph
                </button>
              )}
              {selectedNode.node_type === "Incident" && (
                <button className="kg-btn kg-btn--sm" onClick={() => handleLoadIncident(selectedNode.id)}>
                  View Incident Graph
                </button>
              )}
              {selectedNode.node_type === "Zone" && selectedNode.properties?.zone_id && (
                <button className="kg-btn kg-btn--sm" onClick={() => handleLoadZone(selectedNode.properties.zone_id)}>
                  View Zone Graph
                </button>
              )}
            </div>
          </aside>
        )}
      </div>
    </main>
  );
}

export default KnowledgeGraph;
