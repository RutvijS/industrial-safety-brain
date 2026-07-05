import { useState } from "react";
import Home from "./pages/Home";
import PlantOverview from "./pages/PlantOverview";
import PlantStatePage from "./pages/PlantState";
import "./App.css";

const TABS = [
  { id: "chat", label: "Safety Chat", icon: "🛡️" },
  { id: "overview", label: "Plant Overview", icon: "🏭" },
  { id: "state", label: "Plant State", icon: "🧠" },
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
    </>
  );
}

export default App;
