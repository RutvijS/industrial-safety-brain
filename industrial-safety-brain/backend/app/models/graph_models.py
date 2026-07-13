"""
graph_models.py -- Pydantic models for the Industrial Knowledge Graph.

These models represent graph nodes, edges, and query responses.
The Knowledge Graph is a structured relationship layer --
it does NOT calculate risk.
"""

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class GraphNode(BaseModel):
    """A node in the knowledge graph."""

    id: str = Field(description="Unique node identifier")
    label: str = Field(description="Display label")
    node_type: str = Field(description="Zone, Equipment, Sensor, Permit, etc.")
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """An edge (relationship) in the knowledge graph."""

    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    relationship: str = Field(description="CONTAINS, HAS_SENSOR, etc.")
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphResponse(BaseModel):
    """A subgraph response containing nodes and edges."""

    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    center_node: Optional[str] = None
    node_count: int = 0
    edge_count: int = 0


class GraphStatus(BaseModel):
    """Knowledge graph statistics."""

    connected: bool = False
    node_count: int = 0
    relationship_count: int = 0
    node_types: Dict[str, int] = Field(default_factory=dict)
    relationship_types: Dict[str, int] = Field(default_factory=dict)
    graph_version: str = "1.0.0"
    last_built: Optional[str] = None


class GraphBuildResult(BaseModel):
    """Result of building the graph from datasets."""

    status: str = "success"
    nodes_created: int = 0
    relationships_created: int = 0
    duration_seconds: float = 0.0
    details: Dict[str, int] = Field(default_factory=dict)


class ZoneGraph(BaseModel):
    """Subgraph for a specific zone."""

    zone: str
    zone_name: str = ""
    graph: GraphResponse = Field(default_factory=GraphResponse)


class EquipmentGraph(BaseModel):
    """Subgraph for a specific equipment."""

    equipment_id: str
    equipment_name: str = ""
    zone: str = ""
    graph: GraphResponse = Field(default_factory=GraphResponse)


class IncidentGraph(BaseModel):
    """Subgraph for a specific incident."""

    incident_id: str
    zone: str = ""
    graph: GraphResponse = Field(default_factory=GraphResponse)
