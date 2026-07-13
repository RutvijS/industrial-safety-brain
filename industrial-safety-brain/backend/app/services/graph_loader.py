"""
graph_loader.py -- Populates Neo4j from existing datasets.

Reads all 5 JSON datasets via DataService and creates:
- 11 node types: Zone, Equipment, Sensor, Permit, Maintenance,
  Incident, Worker, Supervisor, Shift, Hazard, Regulation
- 12 relationship types

Uses MERGE to prevent duplicates. Supports incremental updates.
"""

import time
from typing import Dict, Set

from app.services.data_service import data_service
from app.services.knowledge_graph_service import kg_service
from app.services.plant_state_service import ZONE_METADATA


class GraphLoader:
    """Loads datasets into the Neo4j knowledge graph."""

    def build_graph(self) -> Dict:
        """Build the entire knowledge graph from datasets.

        Returns a summary dict with counts.
        """
        start = time.time()

        # Clear existing graph for clean rebuild
        kg_service.clear_graph()

        counts = {
            "zones": 0,
            "equipment": 0,
            "sensors": 0,
            "permits": 0,
            "maintenance": 0,
            "incidents": 0,
            "workers": 0,
            "supervisors": 0,
            "shifts": 0,
            "hazards": 0,
            "regulations": 0,
            "relationships": 0,
        }

        # Create indexes for performance
        self._create_indexes()

        # Load nodes and relationships
        counts["zones"] = self._load_zones()
        eq_count, sensor_count = self._load_sensors()
        counts["equipment"] = eq_count
        counts["sensors"] = sensor_count
        counts["permits"], w1 = self._load_permits()
        counts["maintenance"] = self._load_maintenance()
        counts["shifts"], w2, sup = self._load_shifts()
        counts["workers"] = w1 + w2  # unique workers tracked via MERGE
        counts["supervisors"] = sup
        inc, haz, reg = self._load_incidents()
        counts["incidents"] = inc
        counts["hazards"] = haz
        counts["regulations"] = reg

        counts["relationships"] = kg_service.get_relationship_count()

        duration = time.time() - start

        return {
            "status": "success",
            "nodes_created": kg_service.get_node_count(),
            "relationships_created": counts["relationships"],
            "duration_seconds": round(duration, 2),
            "details": counts,
        }

    def _create_indexes(self) -> None:
        """Create indexes for efficient lookups."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (z:Zone) ON (z.zone_id)",
            "CREATE INDEX IF NOT EXISTS FOR (e:Equipment) ON (e.equipment_id)",
            "CREATE INDEX IF NOT EXISTS FOR (s:Sensor) ON (s.sensor_id)",
            "CREATE INDEX IF NOT EXISTS FOR (p:Permit) ON (p.permit_id)",
            "CREATE INDEX IF NOT EXISTS FOR (m:Maintenance) ON (m.maintenance_id)",
            "CREATE INDEX IF NOT EXISTS FOR (i:Incident) ON (i.incident_id)",
            "CREATE INDEX IF NOT EXISTS FOR (w:Worker) ON (w.worker_id)",
            "CREATE INDEX IF NOT EXISTS FOR (sup:Supervisor) ON (sup.supervisor_id)",
            "CREATE INDEX IF NOT EXISTS FOR (sh:Shift) ON (sh.shift_id)",
            "CREATE INDEX IF NOT EXISTS FOR (h:Hazard) ON (h.hazard_id)",
            "CREATE INDEX IF NOT EXISTS FOR (r:Regulation) ON (r.regulation_id)",
        ]
        for idx in indexes:
            try:
                kg_service.execute_write(idx)
            except Exception:
                pass  # Index may already exist

    def _load_zones(self) -> int:
        """Create Zone nodes from ZONE_METADATA."""
        count = 0
        for zone_key, meta in ZONE_METADATA.items():
            kg_service.execute_write(
                """
                MERGE (z:Zone {zone_id: $zone_id})
                SET z.name = $name,
                    z.risk_type = $risk_type,
                    z.description = $description
                """,
                {
                    "zone_id": zone_key,
                    "name": meta["zone_name"],
                    "risk_type": meta["risk_type"],
                    "description": meta["description"],
                },
            )
            count += 1
        return count

    def _load_sensors(self) -> tuple:
        """Create Equipment and Sensor nodes from sensor data."""
        sensors = data_service.get_sensors()
        equipment_set: Set[str] = set()
        sensor_count = 0

        for s in sensors:
            # Create Equipment node (MERGE avoids duplicates)
            if s.equipment not in equipment_set:
                kg_service.execute_write(
                    """
                    MERGE (e:Equipment {equipment_id: $eq_id})
                    SET e.zone = $zone
                    """,
                    {"eq_id": s.equipment, "zone": s.zone},
                )
                # Zone CONTAINS Equipment
                kg_service.execute_write(
                    """
                    MATCH (z:Zone {zone_id: $zone})
                    MATCH (e:Equipment {equipment_id: $eq_id})
                    MERGE (z)-[:CONTAINS]->(e)
                    """,
                    {"zone": s.zone, "eq_id": s.equipment},
                )
                equipment_set.add(s.equipment)

            # Create Sensor node
            kg_service.execute_write(
                """
                MERGE (s:Sensor {sensor_id: $sensor_id})
                SET s.zone = $zone,
                    s.equipment = $equipment,
                    s.gas_level = $gas,
                    s.temperature = $temp,
                    s.pressure = $pressure,
                    s.humidity = $humidity,
                    s.vibration = $vibration,
                    s.status = $status
                """,
                {
                    "sensor_id": s.sensor_id,
                    "zone": s.zone,
                    "equipment": s.equipment,
                    "gas": s.gas_level,
                    "temp": s.temperature,
                    "pressure": s.pressure,
                    "humidity": s.humidity,
                    "vibration": s.vibration,
                    "status": s.status,
                },
            )
            # Equipment HAS_SENSOR Sensor
            kg_service.execute_write(
                """
                MATCH (e:Equipment {equipment_id: $eq_id})
                MATCH (s:Sensor {sensor_id: $sensor_id})
                MERGE (e)-[:HAS_SENSOR]->(s)
                """,
                {"eq_id": s.equipment, "sensor_id": s.sensor_id},
            )
            sensor_count += 1

        return len(equipment_set), sensor_count

    def _load_permits(self) -> tuple:
        """Create Permit and Worker nodes from permit data."""
        permits = data_service.get_permits()
        permit_count = 0
        worker_count = 0
        workers_seen: Set[str] = set()

        for p in permits:
            # Permit node
            kg_service.execute_write(
                """
                MERGE (p:Permit {permit_id: $pid})
                SET p.permit_type = $ptype,
                    p.zone = $zone,
                    p.equipment = $equipment,
                    p.status = $status,
                    p.start_time = $start,
                    p.end_time = $end
                """,
                {
                    "pid": p.permit_id,
                    "ptype": p.permit_type,
                    "zone": p.zone,
                    "equipment": p.equipment,
                    "status": p.status,
                    "start": p.start_time,
                    "end": p.end_time,
                },
            )

            # Equipment HAS_PERMIT Permit
            kg_service.execute_write(
                """
                MATCH (e:Equipment {equipment_id: $eq_id})
                MATCH (p:Permit {permit_id: $pid})
                MERGE (e)-[:HAS_PERMIT]->(p)
                """,
                {"eq_id": p.equipment, "pid": p.permit_id},
            )

            # Permit ISSUED_FOR Equipment
            kg_service.execute_write(
                """
                MATCH (p:Permit {permit_id: $pid})
                MATCH (e:Equipment {equipment_id: $eq_id})
                MERGE (p)-[:ISSUED_FOR]->(e)
                """,
                {"pid": p.permit_id, "eq_id": p.equipment},
            )

            # Worker node + ASSIGNED_TO Permit
            if p.issued_to and p.issued_to not in workers_seen:
                kg_service.execute_write(
                    """
                    MERGE (w:Worker {worker_id: $wid})
                    SET w.name = $name
                    """,
                    {"wid": p.issued_to, "name": p.issued_to},
                )
                workers_seen.add(p.issued_to)
                worker_count += 1

            kg_service.execute_write(
                """
                MATCH (w:Worker {worker_id: $wid})
                MATCH (p:Permit {permit_id: $pid})
                MERGE (w)-[:ASSIGNED_TO]->(p)
                """,
                {"wid": p.issued_to, "pid": p.permit_id},
            )

            permit_count += 1

        return permit_count, worker_count

    def _load_maintenance(self) -> int:
        """Create Maintenance nodes from maintenance data."""
        records = data_service.get_maintenance()
        count = 0

        for m in records:
            kg_service.execute_write(
                """
                MERGE (mt:Maintenance {maintenance_id: $mid})
                SET mt.equipment = $equipment,
                    mt.zone = $zone,
                    mt.maintenance_type = $mtype,
                    mt.assigned_engineer = $engineer,
                    mt.status = $status,
                    mt.scheduled_time = $scheduled
                """,
                {
                    "mid": m.maintenance_id,
                    "equipment": m.equipment,
                    "zone": m.zone,
                    "mtype": m.maintenance_type,
                    "engineer": m.assigned_engineer,
                    "status": m.status,
                    "scheduled": m.scheduled_time,
                },
            )

            # Equipment UNDER_MAINTENANCE Maintenance
            kg_service.execute_write(
                """
                MATCH (e:Equipment {equipment_id: $eq_id})
                MATCH (mt:Maintenance {maintenance_id: $mid})
                MERGE (e)-[:UNDER_MAINTENANCE]->(mt)
                """,
                {"eq_id": m.equipment, "mid": m.maintenance_id},
            )
            count += 1

        return count

    def _load_shifts(self) -> tuple:
        """Create Shift, Worker, and Supervisor nodes."""
        shifts = data_service.get_shifts()
        shift_count = 0
        worker_count = 0
        sup_count = 0
        workers_seen: Set[str] = set()
        sups_seen: Set[str] = set()

        for s in shifts:
            # Shift node
            kg_service.execute_write(
                """
                MERGE (sh:Shift {shift_id: $sid})
                SET sh.shift_name = $name,
                    sh.zone = $zone,
                    sh.start_time = $start,
                    sh.end_time = $end
                """,
                {
                    "sid": s.shift_id,
                    "name": s.shift_name,
                    "zone": s.zone,
                    "start": s.start_time,
                    "end": s.end_time,
                },
            )

            # Shift ASSIGNED_TO Zone
            kg_service.execute_write(
                """
                MATCH (sh:Shift {shift_id: $sid})
                MATCH (z:Zone {zone_id: $zone})
                MERGE (sh)-[:ASSIGNED_TO]->(z)
                """,
                {"sid": s.shift_id, "zone": s.zone},
            )

            # Supervisor node
            if s.supervisor_id and s.supervisor_id not in sups_seen:
                kg_service.execute_write(
                    """
                    MERGE (sup:Supervisor {supervisor_id: $supid})
                    SET sup.name = $name
                    """,
                    {"supid": s.supervisor_id, "name": s.supervisor},
                )
                sups_seen.add(s.supervisor_id)
                sup_count += 1

            # Workers
            for i, wid in enumerate(s.worker_ids):
                wname = s.workers[i] if i < len(s.workers) else wid
                if wid not in workers_seen:
                    kg_service.execute_write(
                        """
                        MERGE (w:Worker {worker_id: $wid})
                        SET w.name = $name
                        """,
                        {"wid": wid, "name": wname},
                    )
                    workers_seen.add(wid)
                    worker_count += 1

                # Worker WORKS_IN Zone
                kg_service.execute_write(
                    """
                    MATCH (w:Worker {worker_id: $wid})
                    MATCH (z:Zone {zone_id: $zone})
                    MERGE (w)-[:WORKS_IN]->(z)
                    """,
                    {"wid": wid, "zone": s.zone},
                )

            shift_count += 1

        return shift_count, worker_count, sup_count

    def _load_incidents(self) -> tuple:
        """Create Incident, Hazard, and Regulation nodes."""
        incidents = data_service.get_incidents()
        inc_count = 0
        hazards_seen: Set[str] = set()
        regs_seen: Set[str] = set()

        for inc in incidents:
            # Incident node
            kg_service.execute_write(
                """
                MERGE (i:Incident {incident_id: $iid})
                SET i.date = $date,
                    i.zone = $zone,
                    i.equipment = $equipment,
                    i.description = $desc,
                    i.root_cause = $cause,
                    i.severity = $severity,
                    i.injuries = $injuries,
                    i.corrective_action = $action,
                    i.lessons_learned = $lessons
                """,
                {
                    "iid": inc.incident_id,
                    "date": inc.date,
                    "zone": inc.zone,
                    "equipment": inc.equipment,
                    "desc": inc.description,
                    "cause": inc.root_cause,
                    "severity": inc.severity,
                    "injuries": inc.injuries,
                    "action": inc.corrective_action,
                    "lessons": inc.lessons_learned,
                },
            )

            # Incident INVOLVES Equipment
            kg_service.execute_write(
                """
                MATCH (i:Incident {incident_id: $iid})
                MATCH (e:Equipment {equipment_id: $eq_id})
                MERGE (i)-[:INVOLVES]->(e)
                """,
                {"iid": inc.incident_id, "eq_id": inc.equipment},
            )

            # Incident OCCURRED_IN Zone
            kg_service.execute_write(
                """
                MATCH (i:Incident {incident_id: $iid})
                MATCH (z:Zone {zone_id: $zone})
                MERGE (i)-[:OCCURRED_IN]->(z)
                """,
                {"iid": inc.incident_id, "zone": inc.zone},
            )

            # Hazard node from root_cause
            hazard_id = inc.root_cause.lower().replace(" ", "_")[:50]
            if hazard_id and hazard_id not in hazards_seen:
                kg_service.execute_write(
                    """
                    MERGE (h:Hazard {hazard_id: $hid})
                    SET h.name = $name
                    """,
                    {"hid": hazard_id, "name": inc.root_cause},
                )
                hazards_seen.add(hazard_id)

            # Incident RELATED_TO Hazard
            kg_service.execute_write(
                """
                MATCH (i:Incident {incident_id: $iid})
                MATCH (h:Hazard {hazard_id: $hid})
                MERGE (i)-[:RELATED_TO]->(h)
                """,
                {"iid": inc.incident_id, "hid": hazard_id},
            )

            # Regulation node
            reg_id = inc.related_regulation.lower().replace(" ", "_")[:50] if inc.related_regulation else ""
            if reg_id and reg_id not in regs_seen:
                kg_service.execute_write(
                    """
                    MERGE (r:Regulation {regulation_id: $rid})
                    SET r.name = $name
                    """,
                    {"rid": reg_id, "name": inc.related_regulation},
                )
                regs_seen.add(reg_id)

                # Hazard GOVERNED_BY Regulation
                kg_service.execute_write(
                    """
                    MATCH (h:Hazard {hazard_id: $hid})
                    MATCH (r:Regulation {regulation_id: $rid})
                    MERGE (h)-[:GOVERNED_BY]->(r)
                    """,
                    {"hid": hazard_id, "rid": reg_id},
                )

            inc_count += 1

        return inc_count, len(hazards_seen), len(regs_seen)


# Singleton
graph_loader = GraphLoader()
