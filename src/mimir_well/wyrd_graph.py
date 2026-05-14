"""
Mímir's Well — Wyrd Graph Edge Layer
======================================
Multi-hop relationship traversal over Mímir entities.

Every memory is a node. Every relationship is an edge. The Web connects them all.

ᚹ ᛃ ᚱ ᛞ — The Web that binds all things.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WyrdGraph:
    """Multi-hop relationship graph over Mímir entities.

    The Wyrd Graph enables traversal across relationship edges —
    following the threads of fate that connect entities through
    time, space, and meaning.

    Usage:
        graph = WyrdGraph(db_path="/path/to/mimir.db")
        graph.add_edge("runa", "volmarr", "partner", strength=10.0)
        results = graph.traverse("runa", max_depth=3)
        neighborhood = graph.get_related("runa")
    """

    def __init__(self, db_path: str):
        """Connect to the Mímir database and ensure wyrd_edges exists.

        Args:
            db_path: Path to the SQLite database file.
        """
        self._db = sqlite3.connect(db_path)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA busy_timeout=5000")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.row_factory = sqlite3.Row

        # Ensure the table exists (idempotent)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS wyrd_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entity TEXT NOT NULL,
                target_entity TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                strength REAL DEFAULT 1.0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                metadata TEXT DEFAULT '{}',
                user_id TEXT DEFAULT 'runa',
                UNIQUE(source_entity, target_entity, relationship_type, user_id)
            )
        """)
        # Add user_id column if upgrading from older schema
        try:
            self._db.execute("ALTER TABLE wyrd_edges ADD COLUMN user_id TEXT DEFAULT 'runa'")
        except sqlite3.OperationalError:
            pass  # Column already exists
        # Ensure indexes exist
        for idx_sql in [
            "CREATE INDEX IF NOT EXISTS idx_wyrd_edges_source ON wyrd_edges(source_entity)",
            "CREATE INDEX IF NOT EXISTS idx_wyrd_edges_target ON wyrd_edges(target_entity)",
            "CREATE INDEX IF NOT EXISTS idx_wyrd_edges_type ON wyrd_edges(relationship_type)",
            "CREATE INDEX IF NOT EXISTS idx_wyrd_edges_strength ON wyrd_edges(strength)",
            "CREATE INDEX IF NOT EXISTS idx_wyrd_edges_user ON wyrd_edges(user_id)",
        ]:
            self._db.execute(idx_sql)
        self._db.commit()

    def close(self):
        """Close the database connection."""
        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ── Edge Operations ──────────────────────────────────────────────────────

    def add_edge(
        self,
        source: str,
        target: str,
        relationship_type: str,
        strength: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: str = "runa",
    ) -> int:
        """Add or update a directed edge between two entities.

        Uses UPSERT (ON CONFLICT DO UPDATE) so calling add_edge
        on an existing (source, target, relationship_type) triple
        will update the strength and metadata rather than failing.

        Args:
            source: Source entity ID (e.g., "runa").
            target: Target entity ID (e.g., "volmarr").
            relationship_type: Type of relationship (e.g., "partner", "knows").
            strength: Relationship strength 0.0–10.0 (default 1.0).
            metadata: Optional JSON metadata dict.
            user_id: User namespace for multi-tenant isolation (default 'runa').

        Returns:
            The row ID of the inserted/updated edge.
        """
        metadata_json = json.dumps(metadata or {})
        cursor = self._db.execute(
            """
            INSERT INTO wyrd_edges (source_entity, target_entity, relationship_type, strength, metadata, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_entity, target_entity, relationship_type, user_id)
            DO UPDATE SET strength=excluded.strength,
                          metadata=excluded.metadata,
                          updated_at=datetime('now')
            """,
            (source, target, relationship_type, strength, metadata_json, user_id),
        )
        self._db.commit()
        return cursor.lastrowid

    def remove_edge(self, source: str, target: str, relationship_type: str,
                     user_id: Optional[str] = None) -> bool:
        """Remove a specific edge.

        Args:
            source: Source entity ID.
            target: Target entity ID.
            relationship_type: Type of relationship.
            user_id: Filter by user namespace (None = all users).

        Returns:
            True if an edge was removed, False if not found.
        """
        if user_id:
            cursor = self._db.execute(
                """
                DELETE FROM wyrd_edges
                WHERE source_entity = ? AND target_entity = ?
                      AND relationship_type = ? AND user_id = ?
                """,
                (source, target, relationship_type, user_id),
            )
        else:
            cursor = self._db.execute(
                """
                DELETE FROM wyrd_edges
                WHERE source_entity = ? AND target_entity = ? AND relationship_type = ?
                """,
                (source, target, relationship_type),
            )
        self._db.commit()
        return cursor.rowcount > 0

    def get_edge(self, source: str, target: str, relationship_type: str,
                  user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a specific edge by its triple.

        Args:
            source: Source entity ID.
            target: Target entity ID.
            relationship_type: Type of relationship.
            user_id: Filter by user namespace (None = all users).

        Returns:
            Edge dict or None if not found.
        """
        if user_id:
            row = self._db.execute(
                """
                SELECT id, source_entity, target_entity, relationship_type,
                       strength, created_at, updated_at, metadata, user_id
                FROM wyrd_edges
                WHERE source_entity = ? AND target_entity = ?
                      AND relationship_type = ? AND user_id = ?
                """,
                (source, target, relationship_type, user_id),
            ).fetchone()
        else:
            row = self._db.execute(
                """
                SELECT id, source_entity, target_entity, relationship_type,
                       strength, created_at, updated_at, metadata, user_id
                FROM wyrd_edges
                WHERE source_entity = ? AND target_entity = ? AND relationship_type = ?
                """,
                (source, target, relationship_type),
            ).fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "source_entity": row["source_entity"],
            "target_entity": row["target_entity"],
            "relationship_type": row["relationship_type"],
            "strength": row["strength"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "user_id": row["user_id"],
        }

    def get_edges_from(self, entity: str, relationship_type: Optional[str] = None,
                        user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all outgoing edges from an entity.

        Args:
            entity: Source entity ID.
            relationship_type: Optional filter by relationship type.
            user_id: Filter by user namespace (None = all users).

        Returns:
            List of edge dicts.
        """
        if relationship_type and user_id:
            rows = self._db.execute(
                """
                SELECT id, source_entity, target_entity, relationship_type,
                       strength, metadata, created_at, updated_at
                FROM wyrd_edges
                WHERE source_entity = ? AND relationship_type = ? AND user_id = ?
                ORDER BY strength DESC
                """,
                (entity, relationship_type, user_id),
            ).fetchall()
        elif relationship_type:
            rows = self._db.execute(
                """
                SELECT id, source_entity, target_entity, relationship_type,
                       strength, metadata, created_at, updated_at
                FROM wyrd_edges
                WHERE source_entity = ? AND relationship_type = ?
                ORDER BY strength DESC
                """,
                (entity, relationship_type),
            ).fetchall()
        elif user_id:
            rows = self._db.execute(
                """
                SELECT id, source_entity, target_entity, relationship_type,
                       strength, metadata, created_at, updated_at
                FROM wyrd_edges
                WHERE source_entity = ? AND user_id = ?
                ORDER BY strength DESC
                """,
                (entity, user_id),
            ).fetchall()
        else:
            rows = self._db.execute(
                """
                SELECT id, source_entity, target_entity, relationship_type,
                       strength, metadata, created_at, updated_at
                FROM wyrd_edges
                WHERE source_entity = ?
                ORDER BY strength DESC
                """,
                (entity,),
            ).fetchall()

        return [
            {
                "id": r["id"],
                "source": r["source_entity"],
                "target": r["target_entity"],
                "relationship": r["relationship_type"],
                "strength": r["strength"],
                "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]

    def get_edges_to(self, entity: str, relationship_type: Optional[str] = None,
                      user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all incoming edges to an entity.

        Args:
            entity: Target entity ID.
            relationship_type: Optional filter by relationship type.
            user_id: Filter by user namespace (None = all users).

        Returns:
            List of edge dicts.
        """
        if relationship_type and user_id:
            rows = self._db.execute(
                """
                SELECT id, source_entity, target_entity, relationship_type,
                       strength, metadata, created_at, updated_at
                FROM wyrd_edges
                WHERE target_entity = ? AND relationship_type = ? AND user_id = ?
                ORDER BY strength DESC
                """,
                (entity, relationship_type, user_id),
            ).fetchall()
        elif relationship_type:
            rows = self._db.execute(
                """
                SELECT id, source_entity, target_entity, relationship_type,
                       strength, metadata, created_at, updated_at
                FROM wyrd_edges
                WHERE target_entity = ? AND relationship_type = ?
                ORDER BY strength DESC
                """,
                (entity, relationship_type),
            ).fetchall()
        elif user_id:
            rows = self._db.execute(
                """
                SELECT id, source_entity, target_entity, relationship_type,
                       strength, metadata, created_at, updated_at
                FROM wyrd_edges
                WHERE target_entity = ? AND user_id = ?
                ORDER BY strength DESC
                """,
                (entity, user_id),
            ).fetchall()
        else:
            rows = self._db.execute(
                """
                SELECT id, source_entity, target_entity, relationship_type,
                       strength, metadata, created_at, updated_at
                FROM wyrd_edges
                WHERE target_entity = ?
                ORDER BY strength DESC
                """,
                (entity,),
            ).fetchall()

        return [
            {
                "id": r["id"],
                "source": r["source_entity"],
                "target": r["target_entity"],
                "relationship": r["relationship_type"],
                "strength": r["strength"],
                "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]

    # ── Traversal ─────────────────────────────────────────────────────────────

    def traverse(
        self,
        start: str,
        relationship_type: Optional[str] = None,
        max_depth: int = 3,
        min_strength: float = 0.0,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """BFS traversal from start entity, following outgoing edges.

        Like following the threads of the Norns outward from a single point —
        each hop reveals another layer of connection.

        Args:
            start: Entity ID to start from.
            relationship_type: Optional filter by relationship type.
            max_depth: Maximum traversal depth (default 3).
            min_strength: Minimum edge strength to follow (default 0.0).
            user_id: Filter by user namespace (None = all users).

        Returns:
            List of dicts with: entity, distance, path, relationship, strength.
        """
        visited = {start}
        queue = deque([(start, 0, [])])
        results = []

        while queue:
            current, depth, path = queue.popleft()
            if depth >= max_depth:
                continue

            # Get outgoing edges
            sql = """
                SELECT target_entity, relationship_type, strength
                FROM wyrd_edges
                WHERE source_entity = ?
            """
            params: list = [current]
            if relationship_type:
                sql += " AND relationship_type = ?"
                params.append(relationship_type)
            if min_strength > 0:
                sql += " AND strength >= ?"
                params.append(min_strength)
            if user_id:
                sql += " AND user_id = ?"
                params.append(user_id)

            for row in self._db.execute(sql, params).fetchall():
                target = row["target_entity"]
                rel_type = row["relationship_type"]
                strength = row["strength"]

                if target not in visited:
                    visited.add(target)
                    new_path = path + [(current, rel_type, target, strength)]
                    results.append({
                        "entity": target,
                        "distance": depth + 1,
                        "path": new_path,
                        "relationship": rel_type,
                        "strength": strength,
                    })
                    queue.append((target, depth + 1, new_path))

        return results

    def _get_incoming(
        self,
        entity: str,
        max_depth: int = 2,
        min_strength: float = 0.0,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Traverse incoming edges (entities pointing TO this entity).

        Args:
            entity: Entity ID to start from.
            max_depth: Maximum reverse traversal depth.
            min_strength: Minimum edge strength to follow.
            user_id: Filter by user namespace (None = all users).

        Returns:
            List of dicts with: entity, distance, path, relationship, strength.
        """
        visited = {entity}
        queue = deque([(entity, 0, [])])
        results = []

        while queue:
            current, depth, path = queue.popleft()
            if depth >= max_depth:
                continue

            sql = """
                SELECT source_entity, relationship_type, strength
                FROM wyrd_edges
                WHERE target_entity = ?
            """
            params: list = [current]
            if min_strength > 0:
                sql += " AND strength >= ?"
                params.append(min_strength)
            if user_id:
                sql += " AND user_id = ?"
                params.append(user_id)

            for row in self._db.execute(sql, params).fetchall():
                source = row["source_entity"]
                rel_type = row["relationship_type"]
                strength = row["strength"]

                if source not in visited:
                    visited.add(source)
                    new_path = path + [(source, rel_type, current, strength)]
                    results.append({
                        "entity": source,
                        "distance": depth + 1,
                        "path": new_path,
                        "relationship": rel_type,
                        "strength": strength,
                    })
                    queue.append((source, depth + 1, new_path))

        return results

    def get_related(self, entity: str, max_depth: int = 2,
                    user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get all entities related to this entity within max_depth hops.

        Combines outgoing and incoming traversals into a complete
        neighborhood picture — the web of wyrd around a single thread.

        Args:
            entity: Entity ID to explore.
            max_depth: Maximum traversal depth (default 2).
            user_id: Filter by user namespace (None = all users).

        Returns:
            Dict with: entity, outgoing, incoming, total_connections.
        """
        outgoing = self.traverse(entity, max_depth=max_depth, user_id=user_id)
        incoming = self._get_incoming(entity, max_depth=max_depth, user_id=user_id)

        return {
            "entity": entity,
            "outgoing": outgoing,
            "incoming": incoming,
            "total_connections": len(outgoing) + len(incoming),
        }

    # ── Statistics ─────────────────────────────────────────────────────────────

    def edge_count(self, user_id: Optional[str] = None) -> int:
        """Return total number of edges in the graph, optionally filtered by user."""
        if user_id:
            row = self._db.execute(
                "SELECT COUNT(*) FROM wyrd_edges WHERE user_id = ?", (user_id,)
            ).fetchone()
        else:
            row = self._db.execute("SELECT COUNT(*) FROM wyrd_edges").fetchone()
        return row[0] if row else 0

    def entity_count(self, user_id: Optional[str] = None) -> int:
        """Return number of distinct entities in the graph, optionally filtered by user."""
        if user_id:
            row = self._db.execute(
                "SELECT COUNT(DISTINCT e) FROM ("
                "  SELECT source_entity AS e FROM wyrd_edges WHERE user_id = ?"
                "  UNION"
                "  SELECT target_entity AS e FROM wyrd_edges WHERE user_id = ?"
                ")",
                (user_id, user_id),
            ).fetchone()
        else:
            row = self._db.execute(
                "SELECT COUNT(DISTINCT e) FROM ("
                "  SELECT source_entity AS e FROM wyrd_edges "
                "  UNION "
                "  SELECT target_entity AS e FROM wyrd_edges"
                ")"
            ).fetchone()
        return row[0] if row else 0

    def relationship_types(self, user_id: Optional[str] = None) -> List[str]:
        """Return all distinct relationship types in the graph, optionally filtered by user."""
        if user_id:
            rows = self._db.execute(
                "SELECT DISTINCT relationship_type FROM wyrd_edges WHERE user_id = ? ORDER BY relationship_type",
                (user_id,),
            ).fetchall()
        else:
            rows = self._db.execute(
                "SELECT DISTINCT relationship_type FROM wyrd_edges ORDER BY relationship_type"
            ).fetchall()
        return [r[0] for r in rows]

    # ── Migration ─────────────────────────────────────────────────────────────

    def merge_from_fact_store(self, fact_store_path: str) -> Dict[str, int]:
        """One-time migration: import relationship facts from fact_store into wyrd_edges.

        Reads the fact_store SQLite database and creates wyrd_edges entries
        for every relationship fact with two or more entities.

        Args:
            fact_store_path: Path to the fact_store.db file.

        Returns:
            Dict with: edges_created, edges_skipped, total_facts.
        """
        edges_created = 0
        edges_skipped = 0
        total_facts = 0

        try:
            fs_conn = sqlite3.connect(fact_store_path)
            fs_conn.row_factory = sqlite3.Row

            for row in fs_conn.execute(
                "SELECT content, entities, category, tags FROM facts WHERE category = 'relationship'"
            ).fetchall():
                total_facts += 1
                try:
                    entities = json.loads(row["entities"]) if row["entities"] else []
                    if len(entities) >= 2:
                        self.add_edge(
                            source=entities[0],
                            target=entities[1],
                            relationship_type=row["category"],
                            strength=1.0,
                            metadata={
                                "source": "fact_store_migration",
                                "content": row["content"],
                                "tags": row["tags"] if row["tags"] else "",
                            },
                        )
                        edges_created += 1
                    else:
                        edges_skipped += 1
                except (json.JSONDecodeError, IndexError, TypeError):
                    edges_skipped += 1

            fs_conn.close()
        except sqlite3.OperationalError as e:
            logger.error("Fact store migration failed: %s", e)
            return {"edges_created": 0, "edges_skipped": 0, "total_facts": 0, "error": str(e)}

        logger.info(
            "Wyrd Graph migration: %d edges created, %d skipped, %d total facts",
            edges_created,
            edges_skipped,
            total_facts,
        )
        return {
            "edges_created": edges_created,
            "edges_skipped": edges_skipped,
            "total_facts": total_facts,
        }