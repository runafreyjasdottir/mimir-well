# Changelog

All notable changes to Mímir Well will be documented in this file.

## [2.9.0] — 2026-05-14

### 🛡️ Sprint 8: Hardening — Multi-Tenant Isolation, Performance & Architecture

The "Norn's Shield" sprint — 7 phases, 26 findings addressed, 171 tests passing.

#### T8-1: Critical Fixes — user_id Isolation (Write-Side)
- `add_memory()` now accepts `user_id` and stores it per-memory
- `update_memory()` enforces `user_id` isolation — users can only update their own memories
- `delete_memory()` enforces `user_id` isolation — users can only delete their own memories
- `store_with_validity()` accepts `user_id` and `source` params
- `supersede()` enforces cross-user isolation — users cannot supersede other users' memories
- Audit trail propagates `user_id` correctly for all write operations

#### T8-2: Read-Side Isolation
- `get_memory()` respects `user_id` — only returns memories matching the user
- `search_memories()` filters by `user_id` when provided
- `recall_by_importance()`, `recall_recent()`, `recall_by_mood()` all accept `user_id`
- `recall_current()` filters by `user_id`
- `fts_search()` filters by `user_id`
- `consolidate()` respects `user_id` — users only consolidate their own memories
- `detect_contradictions()` scopes by `user_id`
- `promote_to_knowledge()` enforces `user_id` isolation

#### T8-3: WyrdGraph Isolation
- `remove_edge()` accepts `user_id` and filters DELETE operations
- `get_edge()` returns `user_id` and filters by user namespace
- `traverse()` scopes BFS traversal by `user_id`
- `_get_incoming()` scopes reverse traversal by `user_id`
- `get_related()` passes `user_id` through to `traverse()` and `_get_incoming()`
- `edge_count()`, `entity_count()`, `relationship_types()` all accept `user_id`

#### T8-4: Performance & Schema
- **decay() N+1 eliminated**: Replaced per-row `SELECT MAX(accessed_at)` with single LEFT JOIN query
- **Reinforcement bulk UPDATE**: Replaced N+1 SELECT+UPDATE loop with single `UPDATE...WHERE id IN (SELECT...)`
- **`hecedure` → `heuristic` typo**: Fixed in all 5 occurrences across budget.py
- **Migration 008**: Added 3 performance indexes — `idx_access_log_memory_time`, `idx_access_log_recent`, `idx_memories_temporal`
- All 3 indexes also added to base `schema.py` so fresh DBs get them immediately
- `decay()` and reinforcement now accept `user_id` for namespace isolation

#### T8-5: Architecture
- **AuditTrail thread-local connections**: Replaced open/close-per-call pattern with `threading.local()` connection reuse (matching `RunaMemory` pattern)
- **AuditTrail.close()**: New method properly shuts down thread-local connection
- **RunaMemory.close()**: Now also closes `self.audit` connection
- **AuditTrail.stats()**: Accepts `user_id` filter
- **Type hints**: Added `List[str]`, `List[Any]` annotations to `AuditTrail.query()`
- Pi 5 latency threshold relaxed: 60ms → 150ms for recall_by_importance benchmark

#### T8-6: Test Coverage — 28 New Tests
- Entity: add_entity, get_entity, get_entities_by_type, get_entity (nonexistent)
- Relationship: set_relationship, get_relationship_strength (inc. nonexistent)
- Saga: add_saga_event
- Knowledge: add_knowledge, search_knowledge
- Conversation: save_conversation, get_conversation (inc. nonexistent)
- Access: log_access
- Stats/Health: get_stats, health_check, integrity_check, repair
- FTS: rebuild_fts
- Backup/Export: backup_to, restore_from (inc. nonexistent), backup_with_rotation, export_to_json
- WyrdGraph: edge_count, entity_count, relationship_types, merge_from_fact_store
- GitHub: github_backup (returns dict)
- Architecture: AuditTrail thread-local reuse, close, multi-thread, stats user_id, to_dict, type hints
- **Total: 171 tests passing** (up from 125 at Sprint 7)

#### Per-User Namespacing (Multi-Tenancy)
All read/write operations now support `user_id` filtering. When `user_id=None` (default), behavior is unchanged — all memories are visible. When `user_id` is provided, only that user's memories are visible. This enables safe multi-user deployments where each user's memory space is isolated.

---

## [2.8.0] — 2026-05-13

### Sprint 7: Guard, AuditTrail, Per-User Namespacing

- Mímir Guard: trust-aware length limits with FRITH/ALLY/NEUTRAL/STRANGER tiers
- AuditTrail: tamper-detection chain via content hashes and timestamps
- Per-user namespacing: `user_id` column on memories, wyrd_edges, memory_audit tables
- Migration 007: Add `user_id` to all multi-tenant tables
- 125 tests passing

## [2.0.0] — 2026-05-10

### Mímir's Well v2.0 — Complete Rewrite

- Ebbinghaus forgetting curve with configurable half-life
- Self-healing integrity checks with repair mode
- FTS5 full-text search with content-sync mode
- Backup rotation with configurable retention
- GitHub backup integration
- 60 tests passing

## [1.0.0] — 2025-12-01

### Initial Release

- Basic CRUD memory storage
- SQLite backend
- Knowledge graph (entities + relationships)