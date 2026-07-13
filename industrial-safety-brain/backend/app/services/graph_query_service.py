"""
graph_query_service.py -- Reusable graph query functions.

Provides business-level queries against the Knowledge Graph.
All Cypher is encapsulated here -- routes never see raw Cypher.

The Knowledge Graph does NOT calculate risk.
It only provides structured relationships.
"""

from datetime import datetime
from typing import List, Optional

from app.models.graph_models import (
    EquipmentGraph,
    GraphEdge,
    GraphNode,
    GraphResponse,
    GraphStatus,
    IncidentGraph,
    ZoneGraph,
)
from app.services.knowledge_graph_service import kg_service


class GraphQueryService:
    """Encapsulates all graph queries. No raw Cypher in routes."""

    def get_status(self) -> GraphStatus:
        """Return graph statistics."""
        try:
            connected = kg_service.is_connected
            if not connected:
                return GraphStatus(connected=False)

            return GraphStatus(
                connected=True,
                node_count=kg_service.get_node_count(),
                relationship_count=kg_service.get_relationship_count(),
                node_types=kg_service.get_node_type_counts(),
                relationship_types=kg_service.get_relationship_type_counts(),
                graph_version="1.0.0",
                last_built=datetime.utcnow().isoformat(),
            )
        except Exception:
            return GraphStatus(connected=False)

    def get_zone_graph(self, zone_id: str) -> ZoneGraph:
        """Return the subgraph for a specific zone.

        Includes all equipment, sensors, permits, maintenance,
        incidents, and workers connected to the zone.
        """
        # Get zone info
        zone_results = kg_service.execute_read(
            """
            MATCH (z:Zone {zone_id: $zone})
            RETURN z.zone_id AS id, z.name AS name, z.risk_type AS risk_type
            """,
            {"zone": zone_id},
        )

        zone_name = zone_results[0]["name"] if zone_results else zone_id

        # Get all nodes connected to this zone (2 hops)
        results = kg_service.execute_read(
            """
            MATCH (z:Zone {zone_id: $zone})
            OPTIONAL MATCH (z)-[r1]-(n1)
            OPTIONAL MATCH (n1)-[r2]-(n2)
            RETURN
                z, labels(z)[0] AS z_type,
                n1, labels(n1)[0] AS n1_type,
                n2, labels(n2)[0] AS n2_type,
                r1, type(r1) AS r1_type,
                r2, type(r2) AS r2_type
            LIMIT 200
            """,
            {"zone": zone_id},
        )

        nodes, edges = self._parse_graph_results(results)

        return ZoneGraph(
            zone=zone_id,
            zone_name=zone_name,
            graph=GraphResponse(
                nodes=nodes,
                edges=edges,
                center_node=zone_id,
                node_count=len(nodes),
                edge_count=len(edges),
            ),
        )

    def get_equipment_graph(self, equipment_id: str) -> EquipmentGraph:
        """Return entities connected to a specific equipment."""
        # Get equipment info
        eq_results = kg_service.execute_read(
            """
            MATCH (e:Equipment {equipment_id: $eq})
            RETURN e.equipment_id AS id, e.zone AS zone
            """,
            {"eq": equipment_id},
        )

        zone = eq_results[0]["zone"] if eq_results else ""

        # Get connected nodes
        results = kg_service.execute_read(
            """
            MATCH (e:Equipment {equipment_id: $eq})
            OPTIONAL MATCH (e)-[r1]-(n1)
            OPTIONAL MATCH (n1)-[r2]-(n2)
            WHERE n2 <> e
            RETURN
                e, labels(e)[0] AS e_type,
                n1, labels(n1)[0] AS n1_type,
                n2, labels(n2)[0] AS n2_type,
                r1, type(r1) AS r1_type,
                r2, type(r2) AS r2_type
            LIMIT 150
            """,
            {"eq": equipment_id},
        )

        nodes, edges = self._parse_graph_results(results)

        return EquipmentGraph(
            equipment_id=equipment_id,
            equipment_name=equipment_id,
            zone=zone,
            graph=GraphResponse(
                nodes=nodes,
                edges=edges,
                center_node=equipment_id,
                node_count=len(nodes),
                edge_count=len(edges),
            ),
        )

    def get_incident_graph(self, incident_id: str) -> IncidentGraph:
        """Return entities connected to a specific incident."""
        # Get incident info
        inc_results = kg_service.execute_read(
            """
            MATCH (i:Incident {incident_id: $iid})
            RETURN i.incident_id AS id, i.zone AS zone
            """,
            {"iid": incident_id},
        )

        zone = inc_results[0]["zone"] if inc_results else ""

        # Get neighborhood
        results = kg_service.execute_read(
            """
            MATCH (i:Incident {incident_id: $iid})
            OPTIONAL MATCH (i)-[r1]-(n1)
            OPTIONAL MATCH (n1)-[r2]-(n2)
            WHERE n2 <> i
            RETURN
                i, labels(i)[0] AS i_type,
                n1, labels(n1)[0] AS n1_type,
                n2, labels(n2)[0] AS n2_type,
                r1, type(r1) AS r1_type,
                r2, type(r2) AS r2_type
            LIMIT 150
            """,
            {"iid": incident_id},
        )

        nodes, edges = self._parse_graph_results(results)

        return IncidentGraph(
            incident_id=incident_id,
            zone=zone,
            graph=GraphResponse(
                nodes=nodes,
                edges=edges,
                center_node=incident_id,
                node_count=len(nodes),
                edge_count=len(edges),
            ),
        )

    def search_nodes(self, query: str, node_type: Optional[str] = None) -> List[GraphNode]:
        """Search for nodes by name or ID."""
        if node_type:
            results = kg_service.execute_read(
                f"""
                MATCH (n:{node_type})
                WHERE any(key IN keys(n) WHERE toString(n[key]) CONTAINS $query)
                RETURN n, labels(n)[0] AS ntype
                LIMIT 20
                """,
                {"query": query},
            )
        else:
            results = kg_service.execute_read(
                """
                MATCH (n)
                WHERE any(key IN keys(n) WHERE toString(n[key]) CONTAINS $query)
                RETURN n, labels(n)[0] AS ntype
                LIMIT 20
                """,
                {"query": query},
            )

        nodes = []
        for r in results:
            node_data = r.get("n", {})
            ntype = r.get("ntype", "Unknown")
            if hasattr(node_data, "items"):
                props = dict(node_data.items())
            elif isinstance(node_data, dict):
                props = node_data
            else:
                props = {}

            node_id = (
                props.get(f"{ntype.lower()}_id", "")
                or props.get("name", "")
                or str(id(node_data))
            )

            nodes.append(GraphNode(
                id=str(node_id),
                label=props.get("name", node_id),
                node_type=ntype,
                properties=props,
            ))

        return nodes

    def _parse_graph_results(self, results: List[dict]) -> tuple:
        """Parse Neo4j results into GraphNode and GraphEdge lists."""
        node_map = {}
        edge_set = set()
        edges = []

        for row in results:
            # Process all node columns
            for node_key, type_key in [("z", "z_type"), ("e", "e_type"),
                                        ("i", "i_type"), ("n1", "n1_type"),
                                        ("n2", "n2_type")]:
                node_data = row.get(node_key)
                ntype = row.get(type_key)
                if node_data is None or ntype is None:
                    continue

                if hasattr(node_data, "items"):
                    props = dict(node_data.items())
                elif isinstance(node_data, dict):
                    props = node_data
                else:
                    continue

                node_id = self._extract_node_id(props, ntype)
                if node_id and node_id not in node_map:
                    node_map[node_id] = GraphNode(
                        id=node_id,
                        label=props.get("name", node_id),
                        node_type=ntype,
                        properties=props,
                    )

            # Process relationship columns
            for r_key, r_type_key, src_key, src_type, tgt_key, tgt_type in [
                ("r1", "r1_type", "z", "z_type", "n1", "n1_type"),
                ("r1", "r1_type", "e", "e_type", "n1", "n1_type"),
                ("r1", "r1_type", "i", "i_type", "n1", "n1_type"),
                ("r2", "r2_type", "n1", "n1_type", "n2", "n2_type"),
            ]:
                rel = row.get(r_key)
                rel_type = row.get(r_type_key)
                src_data = row.get(src_key)
                tgt_data = row.get(tgt_key)
                st = row.get(src_type)
                tt = row.get(tgt_type)

                if rel is None or rel_type is None or src_data is None or tgt_data is None:
                    continue
                if st is None or tt is None:
                    continue

                src_props = dict(src_data.items()) if hasattr(src_data, "items") else (src_data if isinstance(src_data, dict) else {})
                tgt_props = dict(tgt_data.items()) if hasattr(tgt_data, "items") else (tgt_data if isinstance(tgt_data, dict) else {})

                src_id = self._extract_node_id(src_props, st)
                tgt_id = self._extract_node_id(tgt_props, tt)

                if src_id and tgt_id:
                    edge_key = (src_id, tgt_id, rel_type)
                    if edge_key not in edge_set:
                        edge_set.add(edge_key)
                        edges.append(GraphEdge(
                            source=src_id,
                            target=tgt_id,
                            relationship=rel_type,
                        ))

        return list(node_map.values()), edges

    @staticmethod
    def _extract_node_id(props: dict, node_type: str) -> str:
        """Extract the primary ID from node properties."""
        id_keys = [
            f"{node_type.lower()}_id",
            "zone_id", "equipment_id", "sensor_id", "permit_id",
            "maintenance_id", "incident_id", "worker_id",
            "supervisor_id", "shift_id", "hazard_id", "regulation_id",
            "name",
        ]
        for key in id_keys:
            val = props.get(key)
            if val:
                return str(val)
        return ""


# Singleton
graph_query_service = GraphQueryService()
