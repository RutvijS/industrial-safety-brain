"""
knowledge_graph.py -- REST endpoints for the Industrial Knowledge Graph.

POST /knowledge-graph/build            - Build graph from datasets
GET  /knowledge-graph/status           - Graph statistics
GET  /knowledge-graph/zone/{zone}      - Zone subgraph
GET  /knowledge-graph/equipment/{eq}   - Equipment neighborhood
GET  /knowledge-graph/incident/{inc}   - Incident neighborhood

The Knowledge Graph does NOT calculate risk.
It provides structured relationships only.
"""

from typing import List, Optional

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, Query

from app.models.graph_models import (
    EquipmentGraph,
    GraphBuildResult,
    GraphNode,
    GraphStatus,
    IncidentGraph,
    ZoneGraph,
)
from app.services.graph_loader import graph_loader
from app.services.graph_query_service import graph_query_service

router = APIRouter(prefix="/knowledge-graph", tags=["Knowledge Graph"])


@router.post("/build", response_model=GraphBuildResult)
async def build_graph() -> GraphBuildResult:
    """Build the knowledge graph from existing datasets.

    Clears existing graph and rebuilds from all 5 datasets.
    Creates 11 node types and 12 relationship types.
    """
    try:
        result = graph_loader.build_graph()
        return GraphBuildResult(**result)
    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Neo4j is not available: {e}. Ensure Neo4j is running.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Graph build failed: {e}",
        )


@router.get("/status", response_model=GraphStatus)
async def get_graph_status() -> GraphStatus:
    """Return knowledge graph statistics."""
    return graph_query_service.get_status()


@router.get("/zone/{zone}", response_model=ZoneGraph)
async def get_zone_graph(zone: str) -> ZoneGraph:
    """Return the subgraph for a specific zone.

    Includes equipment, sensors, permits, maintenance,
    incidents, and workers connected to the zone.
    """
    try:
        return graph_query_service.get_zone_graph(zone)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Neo4j is not available.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Zone graph query failed: {e}")


@router.get("/equipment/{equipment}", response_model=EquipmentGraph)
async def get_equipment_graph(equipment: str) -> EquipmentGraph:
    """Return entities connected to a specific equipment."""
    try:
        return graph_query_service.get_equipment_graph(equipment)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Neo4j is not available.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Equipment query failed: {e}")


@router.get("/incident/{incident}", response_model=IncidentGraph)
async def get_incident_graph(incident: str) -> IncidentGraph:
    """Return the incident neighborhood graph."""
    try:
        return graph_query_service.get_incident_graph(incident)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Neo4j is not available.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Incident query failed: {e}")


@router.get("/search", response_model=List[GraphNode])
async def search_graph(
    q: str = Query(..., description="Search query"),
    node_type: Optional[str] = Query(None, description="Filter by node type"),
) -> List[GraphNode]:
    """Search for nodes by name or ID."""
    try:
        return graph_query_service.search_nodes(q, node_type)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Neo4j is not available.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")
