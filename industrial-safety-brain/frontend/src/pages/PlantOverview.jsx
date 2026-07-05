import SensorTable from "../components/SensorTable";
import PermitTable from "../components/PermitTable";
import MaintenanceTable from "../components/MaintenanceTable";
import ShiftTable from "../components/ShiftTable";
import IncidentTable from "../components/IncidentTable";
import "../PlantOverview.css";

function PlantOverview() {
  return (
    <main className="plant-overview">
      <header className="plant-overview__header">
        <div className="plant-overview__logo">🏭</div>
        <h1 className="plant-overview__title">Plant Overview</h1>
        <p className="plant-overview__subtitle">Real-time Plant Data & Historical Records</p>
      </header>

      <div className="plant-overview__sections">
        <SensorTable />
        <PermitTable />
        <MaintenanceTable />
        <ShiftTable />
        <IncidentTable />
      </div>
    </main>
  );
}

export default PlantOverview;
