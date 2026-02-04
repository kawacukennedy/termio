//! Persistent memory store
//!
//! SQLite-backed storage for conversations and memory entries.

use sqlx::{sqlite::SqlitePoolOptions, Pool, Sqlite};
use std::path::Path;

use crate::error::Result;
use crate::models::{Conversation, MemoryEntry, Message};

/// Persistent memory store backed by SQLite
pub struct MemoryStore {
    pool: Pool<Sqlite>,
}

impl MemoryStore {
    /// Create a new memory store with the given database path
    pub async fn new(db_path: impl AsRef<Path>) -> Result<Self> {
        let db_url = format!("sqlite:{}?mode=rwc", db_path.as_ref().display());

        let pool = SqlitePoolOptions::new()
            .max_connections(5)
            .connect(&db_url)
            .await?;

        let store = Self { pool };
        store.run_migrations().await?;

        Ok(store)
    }

    /// Create an in-memory store for testing
    pub async fn in_memory() -> Result<Self> {
        let pool = SqlitePoolOptions::new()
            .max_connections(1)
            .connect("sqlite::memory:")
            .await?;

        let store = Self { pool };
        store.run_migrations().await?;

        Ok(store)
    }

    /// Run database migrations
    async fn run_migrations(&self) -> Result<()> {
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                messages TEXT NOT NULL,
                context_window TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                vector_timestamp TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_conversations_user_id 
            ON conversations(user_id, created_at);

            CREATE INDEX IF NOT EXISTS idx_conversations_session_id 
            ON conversations(session_id);
            "#,
        )
        .execute(&self.pool)
        .await?;

        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS memory_entries (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB,
                metadata TEXT NOT NULL,
                access_control TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_memory_user_id 
            ON memory_entries(user_id, created_at);
            "#,
        )
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    /// Save a conversation
    pub async fn save_conversation(&self, conversation: &Conversation) -> Result<()> {
        let messages_json = serde_json::to_string(&conversation.messages)?;
        let context_json = serde_json::to_string(&conversation.context_window)?;
        let timestamp_json = serde_json::to_string(&conversation.vector_timestamp)?;

        sqlx::query(
            r#"
            INSERT OR REPLACE INTO conversations 
            (id, user_id, device_id, session_id, messages, context_window, created_at, updated_at, vector_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(conversation.id.to_string())
        .bind(conversation.user_id.to_string())
        .bind(conversation.device_id.to_string())
        .bind(conversation.session_id.to_string())
        .bind(messages_json)
        .bind(context_json)
        .bind(conversation.created_at.to_rfc3339())
        .bind(conversation.updated_at.to_rfc3339())
        .bind(timestamp_json)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    /// Get a conversation by ID
    pub async fn get_conversation(&self, id: &str) -> Result<Option<Conversation>> {
        let row = sqlx::query_as::<_, (String, String, String, String, String, String, String, String, String)>(
            "SELECT id, user_id, device_id, session_id, messages, context_window, created_at, updated_at, vector_timestamp FROM conversations WHERE id = ?"
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?;

        match row {
            Some((id, user_id, device_id, session_id, messages, context_window, created_at, updated_at, vector_timestamp)) => {
                Ok(Some(Conversation {
                    id: id.parse().unwrap(),
                    user_id: user_id.parse().unwrap(),
                    device_id: device_id.parse().unwrap(),
                    session_id: session_id.parse().unwrap(),
                    messages: serde_json::from_str(&messages)?,
                    context_window: serde_json::from_str(&context_window)?,
                    created_at: chrono::DateTime::parse_from_rfc3339(&created_at).unwrap().into(),
                    updated_at: chrono::DateTime::parse_from_rfc3339(&updated_at).unwrap().into(),
                    vector_timestamp: serde_json::from_str(&vector_timestamp)?,
                }))
            }
            None => Ok(None),
        }
    }

    /// Save a memory entry
    pub async fn save_memory_entry(&self, entry: &MemoryEntry) -> Result<()> {
        let metadata_json = serde_json::to_string(&entry.metadata)?;
        let access_json = serde_json::to_string(&entry.access_control)?;
        let embedding_bytes = entry.embedding.as_ref().map(|e| {
            e.iter().flat_map(|f| f.to_le_bytes()).collect::<Vec<u8>>()
        });

        sqlx::query(
            r#"
            INSERT OR REPLACE INTO memory_entries 
            (id, user_id, content, embedding, metadata, access_control, created_at, updated_at, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(&entry.id)
        .bind(entry.user_id.to_string())
        .bind(&entry.content)
        .bind(embedding_bytes)
        .bind(metadata_json)
        .bind(access_json)
        .bind(entry.created_at.to_rfc3339())
        .bind(entry.updated_at.to_rfc3339())
        .bind(entry.version as i64)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    /// Search memory entries by content (simple text search)
    pub async fn search_memory(&self, user_id: &str, query: &str, limit: i32) -> Result<Vec<MemoryEntry>> {
        let rows = sqlx::query_as::<_, (String, String, String, Option<Vec<u8>>, String, String, String, String, i64)>(
            r#"
            SELECT id, user_id, content, embedding, metadata, access_control, created_at, updated_at, version
            FROM memory_entries 
            WHERE user_id = ? AND content LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
            "#
        )
        .bind(user_id)
        .bind(format!("%{}%", query))
        .bind(limit)
        .fetch_all(&self.pool)
        .await?;

        let mut entries = Vec::new();
        for (id, user_id, content, embedding_bytes, metadata, access_control, created_at, updated_at, version) in rows {
            let embedding = embedding_bytes.map(|bytes| {
                bytes.chunks(4)
                    .map(|chunk| f32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
                    .collect()
            });

            entries.push(MemoryEntry {
                id,
                user_id: user_id.parse().unwrap(),
                content,
                embedding,
                metadata: serde_json::from_str(&metadata)?,
                access_control: serde_json::from_str(&access_control)?,
                created_at: chrono::DateTime::parse_from_rfc3339(&created_at).unwrap().into(),
                updated_at: chrono::DateTime::parse_from_rfc3339(&updated_at).unwrap().into(),
                version: version as u32,
            });
        }

        Ok(entries)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use uuid::Uuid;

    #[tokio::test]
    async fn test_conversation_crud() {
        let store = MemoryStore::in_memory().await.unwrap();

        let mut conv = Conversation::default();
        conv.add_message(Message::user("Hello"));
        conv.add_message(Message::assistant("Hi there!"));

        // Save
        store.save_conversation(&conv).await.unwrap();

        // Load
        let loaded = store.get_conversation(&conv.id.to_string()).await.unwrap();
        assert!(loaded.is_some());

        let loaded = loaded.unwrap();
        assert_eq!(loaded.messages.len(), 2);
    }

    #[tokio::test]
    async fn test_memory_entry_crud() {
        let store = MemoryStore::in_memory().await.unwrap();
        let user_id = Uuid::new_v4();

        let entry = MemoryEntry::new(user_id, "Test memory content");
        store.save_memory_entry(&entry).await.unwrap();

        let results = store.search_memory(&user_id.to_string(), "Test", 10).await.unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].content, "Test memory content");
    }
}
