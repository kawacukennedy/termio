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

-- Indexes for conversations
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

-- Indexes for memory entries
CREATE INDEX IF NOT EXISTS idx_memory_user_id 
ON memory_entries(user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_memory_tags 
ON memory_entries(json_extract(metadata, '$.tags'));

-- TTL index for automatic cleanup (30 days)
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
    signature TEXT NOT NULL,  -- JSON object
    installed_at TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1
);

-- Index for plugin lookups
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

-- Index for sync state lookups
CREATE INDEX IF NOT EXISTS idx_sync_user_id 
ON device_sync_state(user_id);
