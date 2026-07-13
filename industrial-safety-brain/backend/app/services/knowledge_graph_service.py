"""
knowledge_graph_service.py -- Neo4j connection and CRUD layer.

Abstract interface for graph database operations.
Business logic never touches Neo4j directly -- all access goes through here.
Designed so another graph DB (e.g. Amazon Neptune, TigerGraph) can be
substituted by reimplementing this class alone.
"""

from typing import Any, Dict, List, Optional

from app.config import settings


class KnowledgeGraphService:
    """Neo4j-backed knowledge graph service.

    Provides CRUD operations and query execution.
    Handles connection pooling and graceful degradation.
    """

    def __init__(self) -> None:
        self._driver = None
        self._initialized = False

    def _ensure_init(self) -> None:
        """Lazy-initialize the Neo4j driver."""
        if self._initialized:
            return

        try:
            # pyrefly: ignore [missing-import]
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
            # Verify connectivity
            self._driver.verify_connectivity()
            self._initialized = True
        except Exception as e:
            self._driver = None
            self._initialized = False
            raise ConnectionError(f"Neo4j connection failed: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if Neo4j is reachable."""
        try:
            self._ensure_init()
            return self._driver is not None
        except Exception:
            return False

    def execute_write(self, cypher: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """Execute a write transaction (CREATE, MERGE, DELETE)."""
        self._ensure_init()
        with self._driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]

    def execute_read(self, cypher: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """Execute a read transaction (MATCH, RETURN)."""
        self._ensure_init()
        with self._driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]

    def execute_write_batch(self, statements: List[tuple]) -> int:
        """Execute multiple write statements in a single transaction.

        Args:
            statements: List of (cypher, params) tuples.

        Returns:
            Number of statements executed.
        """
        self._ensure_init()
        count = 0
        with self._driver.session() as session:
            with session.begin_transaction() as tx:
                for cypher, params in statements:
                    tx.run(cypher, params or {})
                    count += 1
                tx.commit()
        return count

    def clear_graph(self) -> None:
        """Delete all nodes and relationships. Use with caution."""
        self._ensure_init()
        self.execute_write("MATCH (n) DETACH DELETE n")

    def get_node_count(self) -> int:
        """Return total number of nodes."""
        try:
            result = self.execute_read("MATCH (n) RETURN count(n) AS count")
            return result[0]["count"] if result else 0
        except Exception:
            return 0

    def get_relationship_count(self) -> int:
        """Return total number of relationships."""
        try:
            result = self.execute_read("MATCH ()-[r]->() RETURN count(r) AS count")
            return result[0]["count"] if result else 0
        except Exception:
            return 0

    def get_node_type_counts(self) -> Dict[str, int]:
        """Return count of nodes per label."""
        try:
            result = self.execute_read(
                "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count"
            )
            return {r["label"]: r["count"] for r in result if r.get("label")}
        except Exception:
            return {}

    def get_relationship_type_counts(self) -> Dict[str, int]:
        """Return count of relationships per type."""
        try:
            result = self.execute_read(
                "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count"
            )
            return {r["type"]: r["count"] for r in result if r.get("type")}
        except Exception:
            return {}

    def close(self) -> None:
        """Close the driver connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            self._initialized = False


# Singleton
kg_service = KnowledgeGraphService()
