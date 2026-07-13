import { useState } from "react";
import Home from "./pages/Home";
import PlantOverview from "./pages/PlantOverview";
import PlantStatePage from "./pages/PlantState";
import RiskAnalysisPage from "./pages/RiskAnalysis";
import IncidentIntelligencePage from "./pages/IncidentIntelligence";
import PlantHeatmapPage from "./pages/PlantHeatmap";
import KnowledgeGraphPage from "./pages/KnowledgeGraph";
import AgentAnalysisPage from "./pages/AgentAnalysis";
import CompliancePage from "./pages/CompliancePage";
import EmergencyPage from "./pages/EmergencyPage";
import IncidentReportPage from "./pages/IncidentReportPage";
import "./App.css";

const TABS = [
  { id: "chat", label: "Safety Chat", icon: "🛡️" },
  { id: "overview", label: "Plant Overview", icon: "🏭" },
  { id: "state", label: "Plant State", icon: "🧠" },
  { id: "risk", label: "Risk Analysis", icon: "🔥" },
  { id: "intel", label: "Incident Intel", icon: "📚" },
  { id: "heatmap", label: "Heatmap", icon: "🗺️" },
  { id: "graph", label: "Knowledge Graph", icon: "🕸️" },
  { id: "agents", label: "Agent Analysis", icon: "🤖" },
  { id: "compliance", label: "Compliance", icon: "📋" },
  { id: "emergency", label: "Emergency", icon: "🚨" },
  { id: "report", label: "Report", icon: "📄" },
];

function App() {
  const [activeTab, setActiveTab] = useState("chat");

  return (
    <>
      <nav className="app-nav">
        <div className="app-nav__brand">Industrial Safety Brain</div>
        <div className="app-nav__tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`app-nav__tab ${activeTab === tab.id ? "app-nav__tab--active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="app-nav__tab-icon">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      {activeTab === "chat" && <Home />}
      {activeTab === "overview" && <PlantOverview />}
      {activeTab === "state" && <PlantStatePage />}
      {activeTab === "risk" && <RiskAnalysisPage />}
      {activeTab === "intel" && <IncidentIntelligencePage />}
      {activeTab === "heatmap" && <PlantHeatmapPage />}
      {activeTab === "graph" && <KnowledgeGraphPage />}
      {activeTab === "agents" && <AgentAnalysisPage />}
      {activeTab === "compliance" && <CompliancePage />}
      {activeTab === "emergency" && <EmergencyPage />}
      {activeTab === "report" && <IncidentReportPage />}
    </>
  );
}

export default App;
