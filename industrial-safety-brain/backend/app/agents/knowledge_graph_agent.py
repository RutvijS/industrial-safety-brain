"""
knowledge_graph_agent.py -- Knowledge Graph Agent.

Wraps the existing GraphQueryService.
Never duplicates graph logic.

Input:  Zone / Equipment / Incident IDs
Output: Relationship context from Neo4j
"""

from typing import Any, Dict

from app.agents.base_agent import BaseAgent


class KnowledgeGraphAgent(BaseAgent):
    """Wraps GraphQueryService for relationship context."""

    name = "knowledge_graph_agent"
    display_name = "Knowledge Graph Agent"
    icon = "🕸️"

    def validate(self, context: Dict[str, Any]) -> bool:
        return "zone" in context

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from app.services.graph_query_service import graph_query_service

        zone = context["zone"]

        # Get graph status first
        status = graph_query_service.get_status()

        if not status.connected or status.node_count == 0:
            return {
                "available": False,
                "reason": "Knowledge graph not built or Neo4j unavailable",
                "node_count": 0,
                "relationship_count": 0,
            }

        # Get zone subgraph
        try:
            zone_graph = graph_query_service.get_zone_graph(zone)
            graph_data = zone_graph.graph

            # Summarize relationships by type
            rel_summary = {}
            for edge in graph_data.edges:
                rel_summary[edge.relationship] = rel_summary.get(edge.relationship, 0) + 1

            # Summarize node types
            node_summary = {}
            for node in graph_data.nodes:
                node_summary[node.node_type] = node_summary.get(node.node_type, 0) + 1

            return {
                "available": True,
                "zone": zone,
                "zone_name": zone_graph.zone_name,
                "total_nodes": graph_data.node_count,
                "total_edges": graph_data.edge_count,
                "node_types": node_summary,
                "relationship_types": rel_summary,
                "connected_equipment": [
                    n.id for n in graph_data.nodes if n.node_type == "Equipment"
                ],
                "connected_incidents": [
                    n.id for n in graph_data.nodes if n.node_type == "Incident"
                ],
                "connected_workers": [
                    n.id for n in graph_data.nodes if n.node_type == "Worker"
                ],
                "hazards": [
                    {"id": n.id, "name": n.label}
                    for n in graph_data.nodes if n.node_type == "Hazard"
                ],
                "regulations": [
                    {"id": n.id, "name": n.label}
                    for n in graph_data.nodes if n.node_type == "Regulation"
                ],
            }

        except Exception as e:
            return {
                "available": False,
                "reason": str(e),
                "node_count": status.node_count,
                "relationship_count": status.relationship_count,
            }
