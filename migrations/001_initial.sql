-- HEDTRONIX Database Schema
-- SQLite Initial Migration

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    messages TEXT NOT NULL,  -- JSON array of messages
    context_window TEXT NOT NULL,  -- JSON object
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    vector_timestamp TEXT NOT NULL  -- JSON array for CRDT
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id 
ON conversations(user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_conversations_session_id 
ON conversations(session_id);

CREATE INDEX IF NOT EXISTS idx_conversations_updated 
ON conversations(updated_at);

-- Memory entries table
CREATE TABLE IF NOT EXISTS memory_entries (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding BLOB,  -- 768-dimension float32 array
    metadata TEXT NOT NULL,  -- JSON object
    access_control TEXT NOT NULL,  -- JSON object
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_memory_user_id 
ON memory_entries(user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_memory_tags 
ON memory_entries(json_extract(metadata, '$.tags'));

CREATE INDEX IF NOT EXISTS idx_memory_updated 
ON memory_entries(updated_at);

-- Plugin registry table
CREATE TABLE IF NOT EXISTS plugins (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT,
    author TEXT NOT NULL,  -- JSON object
    capabilities TEXT NOT NULL,  -- JSON object
    permissions TEXT NOT NULL,  -- JSON object
    entry_points TEXT NOT NULL, -- JSON object (wasm_module, initialize, cleanup)
    signature TEXT,  -- JSON object
    compatibility TEXT NOT NULL, -- JSON object (min_core_version, platforms)
    installed_at TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_plugins_name 
ON plugins(name);

-- Device sync state table
CREATE TABLE IF NOT EXISTS device_sync_state (
    device_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    last_sync TEXT NOT NULL,  -- JSON object with timestamp, vector_clock, hash
    pending_changes TEXT NOT NULL,  -- JSON object
    connection_info TEXT NOT NULL,  -- JSON object
    sync_config TEXT NOT NULL  -- JSON object
);

CREATE INDEX IF NOT EXISTS idx_sync_user_id 
ON device_sync_state(user_id);

-- Health data table (FA-008)
CREATE TABLE IF NOT EXISTS health_data (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    source TEXT NOT NULL,  -- 'wearable', 'manual', 'device_sensors'
    timestamp TEXT NOT NULL,
    data_type TEXT NOT NULL,  -- 'heart_rate', 'hrv', 'spo2', etc.
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    metadata TEXT NOT NULL  -- JSON object
);

CREATE INDEX IF NOT EXISTS idx_health_user_id 
ON health_data(user_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_health_type 
ON health_data(data_type, timestamp);

-- Action plans table (FA-002 Agentic OS)
CREATE TABLE IF NOT EXISTS action_plans (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    trigger TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    steps TEXT NOT NULL,  -- JSON array of ActionStep
    created_at TEXT NOT NULL,
    completed_at TEXT,
    requires_approval INTEGER NOT NULL DEFAULT 0,
    approval_granted INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_action_plans_user_id 
ON action_plans(user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_action_plans_status 
ON action_plans(status);

-- Knowledge graph nodes table (FA-003)
CREATE TABLE IF NOT EXISTS knowledge_nodes (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    node_type TEXT NOT NULL,  -- 'concept', 'entity', 'event', 'preference'
    label TEXT NOT NULL,
    properties TEXT NOT NULL,  -- JSON object
    embedding BLOB,  -- 768-dimension float32 array
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    access_level TEXT NOT NULL DEFAULT 'private'
);

CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_user 
ON knowledge_nodes(user_id, node_type);

CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_label 
ON knowledge_nodes(label);

-- Knowledge graph edges table (FA-003)
CREATE TABLE IF NOT EXISTS knowledge_edges (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES knowledge_nodes(id),
    target_id TEXT NOT NULL REFERENCES knowledge_nodes(id),
    relationship TEXT NOT NULL,  -- 'related_to', 'causes', 'part_of', 'precedes'
    weight REAL NOT NULL DEFAULT 1.0,
    properties TEXT,  -- JSON object
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_knowledge_edges_source 
ON knowledge_edges(source_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_edges_target 
ON knowledge_edges(target_id);

-- Notifications table (FA-012)
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    device_id TEXT,
    notification_type TEXT NOT NULL DEFAULT 'system',
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium',
    category TEXT NOT NULL DEFAULT 'system',
    icon TEXT,
    data TEXT,  -- JSON object
    delivery_time TEXT,
    expiration TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    personalization TEXT,  -- JSON object
    created_at TEXT NOT NULL,
    read_at TEXT,
    read INTEGER NOT NULL DEFAULT 0,
    dismissed INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_notifications_user 
ON notifications(user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_notifications_status 
ON notifications(status, delivery_time);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    metadata TEXT,  -- JSON object
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_user 
ON documents(user_id, created_at);
