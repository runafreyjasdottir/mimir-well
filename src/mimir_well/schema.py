"""
Mímir's Well — Database Schema Definitions
============================================
SQL CREATE statements, indexes, and FTS5 triggers for the memory database.
"""

# Schema version for migration tracking
SCHEMA_VERSION = 2

# ─── Table creation statements ─────────────────────────────────────────────

MEMORIES_TABLE = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    tags JSON,
    importance INTEGER DEFAULT 5 CHECK(importance >= 1 AND importance <= 10),
    emotional_valence REAL DEFAULT 0.0 CHECK(emotional_valence >= -1.0 AND emotional_valence <= 1.0)
)
"""

SAGA_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS saga_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    entity_id TEXT,
    data JSON,
    participants JSON
)
"""

ENTITIES_TABLE = """
CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    components JSON,
    state JSON,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""

RELATIONSHIPS_TABLE = """
CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_a TEXT NOT NULL,
    entity_b TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    strength INTEGER DEFAULT 5 CHECK(strength >= 1 AND strength <= 10),
    metadata JSON,
    UNIQUE(entity_a, entity_b, relationship_type)
)
"""

CONVERSATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS conversations (
    session_id TEXT PRIMARY KEY,
    participants JSON,
    transcript TEXT,
    summary TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""

KNOWLEDGE_TABLE = """
CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT,
    confidence REAL DEFAULT 1.0 CHECK(confidence >= 0.0 AND confidence <= 1.0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""

MEMORY_ACCESS_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS memory_access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id INTEGER NOT NULL,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_type TEXT DEFAULT 'recall',
    FOREIGN KEY (memory_id) REFERENCES memories(id)
)
"""

# ─── Index creation statements ─────────────────────────────────────────────

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)",
    "CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance)",
    "CREATE INDEX IF NOT EXISTS idx_memories_valence ON memories(emotional_valence)",
    "CREATE INDEX IF NOT EXISTS idx_saga_events_type ON saga_events(event_type)",
    "CREATE INDEX IF NOT EXISTS idx_saga_events_entity ON saga_events(entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_domain ON knowledge(domain)",
    "CREATE INDEX IF NOT EXISTS idx_access_log_memory ON memory_access_log(memory_id)",
    "CREATE INDEX IF NOT EXISTS idx_access_log_time ON memory_access_log(accessed_at)",
]

# ─── FTS5 virtual tables ──────────────────────────────────────────────────

FTS_TABLES = [
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
    USING fts5(content, category, tags, content=memories, content_rowid=id)
    """,
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts
    USING fts5(content, domain, source, content=knowledge, content_rowid=id)
    """,
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS saga_events_fts
    USING fts5(event_type, entity_id, content=saga_events, content_rowid=id)
    """,
]

# ─── FTS sync ──────────────────────────────────────────────────────────────
# With content=external mode, FTS5 auto-syncs on INSERT, UPDATE, and DELETE.
# No triggers are needed — SQLite handles it all internally.
FTS_TRIGGERS = []

# ─── SQLite PRAGMAs ────────────────────────────────────────────────────────

PRAGMAS = [
    "PRAGMA foreign_keys = ON",
    "PRAGMA journal_mode = WAL",
    "PRAGMA busy_timeout = 10000",
    "PRAGMA synchronous = FULL",
    "PRAGMA wal_autocheckpoint = 1000",
    "PRAGMA mmap_size = 0",
]

# ─── All table SQL aggregated for convenience ──────────────────────────────

ALL_TABLES = [
    MEMORIES_TABLE,
    SAGA_EVENTS_TABLE,
    ENTITIES_TABLE,
    RELATIONSHIPS_TABLE,
    CONVERSATIONS_TABLE,
    KNOWLEDGE_TABLE,
    MEMORY_ACCESS_LOG_TABLE,
]