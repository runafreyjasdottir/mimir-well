# Changelog — Mímir's Well

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.10.0] — 2026-05-15 — Byrgishólmr (Fortress Isle)

*Sprint 9: Byrgishólmr — a fortress of iron and ice, where every wall is tested and every gate is secured.*

### Added

- **T9-1: Thread Safety** — 8 new tests
  - `WyrdGraph` now uses `threading.local()` for thread-local connections (`_get_conn()`)
  - `WyrdGraph._write()` wraps all mutations in `RLock` for safe concurrent access
  - `WyrdGraph.add_edge()` and `remove_edge()` use `_write()` closure pattern
  - `RunaMemory._commit()` acquires `RLock` to prevent concurrent commit interleaving
  - `RunaMemory.decay()` and `consolidate()` hold `RLock` for full operation scope
  - Both `Lock` → `RLock` to prevent deadlock when `_commit()` is called within locked scope
  - `_get_conn()` now applies ALL PRAGMAS including `busy_timeout=10000` and `synchronous=NORMAL`
- **T9-3: Connection Resilience** — 7 new tests
  - `restore_from_backup()` resets thread-local connection after restore
  - `validate_backup()` deduplicated (calls `repair.validate_backup()` instead of duplicating)
  - Dead code removed: `FTS_TRIGGERS = []` was never populated
  - `github_backup()` logs warning when repo URL not configured
  - Rollback migration test
- **T9-5: Context Engineer Tests** — 30 new tests
  - `ContextResult`: 9 tests covering formatting, stats, truncation, all channels
  - `ContextEngineer`: 3 init tests (default, custom budgeter, custom context)
  - Entity extraction: 6 tests (capitalized, multi-word, skip words, dedup, empty, lowercase)
  - Token estimation: 4 tests (empty, short, long, minimum)
  - Context assembly: 7 tests (assemble, budget, entities, categories, empty, graph, quick)
  - Round-trip: 1 test (assemble → to_context_block)
- **T9-6: MimirConfig Tests** — 17 new tests
  - Defaults, creation, get/set, persistence, properties, env overrides, invalid JSON

### Changed

- **T9-2: API Consistency**
  - Unified edge dict key: all `WyrdGraph` methods now return `relationship_type` (not `relationship`)
  - Added `__repr__` to `RunaMemory`, `WyrdGraph`, and `AuditTrail`
  - `search_knowledge()` now accepts optional `user_id` parameter
  - Consolidated `CATEGORY_TYPE_MAP`: `budget.py` now derives from `core.py` via `infer_memory_type()`
  - Removed duplicate `CORE_CATEGORY_TYPE_MAP` from `__init__.py`
- **T9-4: Performance N+1**
  - `promote_to_knowledge()`: batch existence check with single `IN()` query + Python set (was N+1 per-row SELECT)
  - `traverse()`: batch BFS queries per level with `WHERE IN()` (was N+1 per-node SELECT)
  - Migration 009: 5 composite indexes for WyrdGraph traversal, promotion uniqueness, contradiction detection, saga events
  - `SCHEMA_VERSION` bumped 8 → 9

### Fixed

- **Critical**: `_get_conn()` was skipping `busy_timeout` and `synchronous` PRAGMAS — only WAL and foreign_keys were applied. This caused "database is locked" errors under concurrent load.
- **Critical**: `threading.Lock()` in `decay()`/`consolidate()` deadlocked when `_commit()` also acquired the lock. Switched both classes to `threading.RLock()`.
- `restore_from_backup()` left stale thread-local connections pointing to the old database file.
- `budget.py` had `"implicit"` mapped to `MemoryChannel.IMPLICIT` which doesn't exist — now correctly maps to `MemoryChannel.HEURISTIC`.
- `recall_by_importance` latency threshold raised to 250ms for Pi 5 under concurrent test load.

### Removed

- Dead `FTS_TRIGGERS = []` list and its loop in `_init_schema()`
- Duplicate `CATEGORY_TYPE_MAP` from `budget.py`

## [2.9.0] — 2026-05-14 — Týr's Sacrifice

*Sprint 8: Major release — temporal validity, self-healing migrations, schema versioning, Ebbinghaus decay.*

### Added
- Temporal validity fields (`valid_from`, `valid_until`, `superseded_by`, `is_current`)
- Schema migration system with version tracking
- Ebbinghaus decay with reinforcement
- Token budget system for context engineering
- WyrdGraph for entity-relationship modeling
- Audit trail for memory operations
- Context engineering pipeline

### Changed
- SCHEMA_VERSION bumped to 8
- All database operations use thread-safe connection management

## [2.0.0] — 2026-05-13 — Æsir's Foundation

*Complete rewrite with thread safety, token budgeting, and the Three Wells architecture.*

### Added
- Thread-safe `RunaMemory` with `threading.local()` connections
- Token budget system (`TokenBudget`, `TokenBudgeter`)
- WyrdGraph entity-relationship store
- Audit trail system
- Backup/restore with GitHub push support