//! Persistent memory store
//!
//! SQLite-backed storage for conversations, memory entries, knowledge graph,
//! health data, action plans, plugins, and notifications.

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
        // Conversations
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
                vector_timestamp TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
            );
            CREATE INDEX IF NOT EXISTS idx_conversations_user_id 
            ON conversations(user_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_conversations_session_id 
            ON conversations(session_id);
            "#,
        )
        .execute(&self.pool)
        .await?;

        // Memory entries
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

        // Knowledge graph nodes (FA-003)
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                node_type TEXT NOT NULL,
                label TEXT NOT NULL,
                properties TEXT NOT NULL DEFAULT '{}',
                embedding BLOB,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                access_level TEXT NOT NULL DEFAULT 'private'
            );
            CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_user
            ON knowledge_nodes(user_id, node_type);
            CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_label
            ON knowledge_nodes(label);
            "#,
        )
        .execute(&self.pool)
        .await?;

        // Knowledge graph edges (FA-003)
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS knowledge_edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                weight REAL NOT NULL DEFAULT 1.0,
                properties TEXT,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_knowledge_edges_source
            ON knowledge_edges(source_id);
            CREATE INDEX IF NOT EXISTS idx_knowledge_edges_target
            ON knowledge_edges(target_id);
            "#,
        )
        .execute(&self.pool)
        .await?;

        // Health data (FA-008)
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS health_data (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                source TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                data_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 1.0,
                metadata TEXT NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_health_user_id
            ON health_data(user_id, timestamp);
            CREATE INDEX IF NOT EXISTS idx_health_type
            ON health_data(data_type, timestamp);
            "#,
        )
        .execute(&self.pool)
        .await?;

        // Action plans (FA-002)
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS action_plans (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                trigger TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                steps TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                requires_approval INTEGER NOT NULL DEFAULT 0,
                approval_granted INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_action_plans_user_id
            ON action_plans(user_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_action_plans_status
            ON action_plans(status);
            "#,
        )
        .execute(&self.pool)
        .await?;

        // Plugins
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS plugins (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                description TEXT,
                author TEXT NOT NULL DEFAULT '{}',
                capabilities TEXT NOT NULL DEFAULT '{}',
                permissions TEXT NOT NULL DEFAULT '{}',
                entry_points TEXT NOT NULL DEFAULT '{}',
                signature TEXT,
                compatibility TEXT NOT NULL DEFAULT '{}',
                installed_at TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_plugins_name
            ON plugins(name);
            "#,
        )
        .execute(&self.pool)
        .await?;

        // Notifications (FA-012)
        sqlx::query(
            r#"
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
                data TEXT,
                delivery_time TEXT,
                expiration TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                personalization TEXT,
                created_at TEXT NOT NULL,
                read_at TEXT,
                read INTEGER NOT NULL DEFAULT 0,
                dismissed INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_notifications_user
            ON notifications(user_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_notifications_status
            ON notifications(status, delivery_time);
            "#,
        )
        .execute(&self.pool)
        .await?;

        // Subscriptions
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                tier TEXT NOT NULL DEFAULT 'freemium',
                status TEXT NOT NULL DEFAULT 'active',
                provider TEXT NOT NULL DEFAULT 'manual',
                provider_subscription_id TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                auto_renew INTEGER NOT NULL DEFAULT 0,
                features TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id
            ON subscriptions(user_id);
            "#,
        )
        .execute(&self.pool)
        .await?;

        // Payment methods
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS payment_methods (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                method_type TEXT NOT NULL DEFAULT 'card',
                details_encrypted TEXT NOT NULL DEFAULT '{}',
                is_default INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_payment_methods_user_id
            ON payment_methods(user_id);
            "#,
        )
        .execute(&self.pool)
        .await?;

        // Smart home devices (FA-006)
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS smart_devices (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                device_type TEXT NOT NULL DEFAULT 'unknown',
                protocol TEXT NOT NULL DEFAULT 'matter',
                is_online INTEGER NOT NULL DEFAULT 1,
                state TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_smart_devices_user_id
            ON smart_devices(user_id);
            "#,
        )
        .execute(&self.pool)
        .await?;

        // Smart home scenes (FA-006)
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS smart_scenes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                actions TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_smart_scenes_user_id
            ON smart_scenes(user_id);
            "#,
        )
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    // ======================================================================
    // Conversations
    // ======================================================================

    /// Save a conversation
    pub async fn save_conversation(&self, conversation: &Conversation) -> Result<()> {
        let messages_json = serde_json::to_string(&conversation.messages)?;
        let context_json = serde_json::to_string(&conversation.context_window)?;
        let timestamp_json = serde_json::to_string(&conversation.vector_timestamp)?;
        let status = &conversation.status;

        sqlx::query(
            r#"
            INSERT OR REPLACE INTO conversations 
            (id, user_id, device_id, session_id, messages, context_window, created_at, updated_at, vector_timestamp, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        .bind(status)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    /// Get a conversation by ID
    pub async fn get_conversation(&self, id: &str) -> Result<Option<Conversation>> {
        let row = sqlx::query_as::<_, (String, String, String, String, String, String, String, String, String, String)>(
            "SELECT id, user_id, device_id, session_id, messages, context_window, created_at, updated_at, vector_timestamp, status FROM conversations WHERE id = ?"
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?;

        match row {
            Some((id, user_id, device_id, session_id, messages, context_window, created_at, updated_at, vector_timestamp, status)) => {
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
                    status,
                }))
            }
            None => Ok(None),
        }
    }

    /// List conversations for a user, ordered by most recent
    pub async fn list_conversations(&self, user_id: &str, limit: i32) -> Result<Vec<Conversation>> {
        let rows = sqlx::query_as::<_, (String, String, String, String, String, String, String, String, String, String)>(
            r#"
            SELECT id, user_id, device_id, session_id, messages, context_window, created_at, updated_at, vector_timestamp, status
            FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT ?
            "#,
        )
        .bind(user_id)
        .bind(limit)
        .fetch_all(&self.pool)
        .await?;

        let mut convs = Vec::new();
        for (id, user_id, device_id, session_id, messages, context_window, created_at, updated_at, vector_timestamp, status) in rows {
            convs.push(Conversation {
                id: id.parse().unwrap(),
                user_id: user_id.parse().unwrap(),
                device_id: device_id.parse().unwrap(),
                session_id: session_id.parse().unwrap(),
                messages: serde_json::from_str(&messages)?,
                context_window: serde_json::from_str(&context_window)?,
                created_at: chrono::DateTime::parse_from_rfc3339(&created_at).unwrap().into(),
                updated_at: chrono::DateTime::parse_from_rfc3339(&updated_at).unwrap().into(),
                vector_timestamp: serde_json::from_str(&vector_timestamp)?,
                status,
            });
        }
        Ok(convs)
    }

    /// List all conversations (no user filter), ordered by most recent
    pub async fn list_all_conversations(&self, limit: i32) -> Result<Vec<Conversation>> {
        let rows = sqlx::query_as::<_, (String, String, String, String, String, String, String, String, String, String)>(
            r#"
            SELECT id, user_id, device_id, session_id, messages, context_window, created_at, updated_at, vector_timestamp, status
            FROM conversations
            ORDER BY updated_at DESC
            LIMIT ?
            "#,
        )
        .bind(limit)
        .fetch_all(&self.pool)
        .await?;

        let mut convs = Vec::new();
        for (id, user_id, device_id, session_id, messages, context_window, created_at, updated_at, vector_timestamp, status) in rows {
            convs.push(Conversation {
                id: id.parse().unwrap(),
                user_id: user_id.parse().unwrap(),
                device_id: device_id.parse().unwrap(),
                session_id: session_id.parse().unwrap(),
                messages: serde_json::from_str(&messages)?,
                context_window: serde_json::from_str(&context_window)?,
                created_at: chrono::DateTime::parse_from_rfc3339(&created_at).unwrap().into(),
                updated_at: chrono::DateTime::parse_from_rfc3339(&updated_at).unwrap().into(),
                vector_timestamp: serde_json::from_str(&vector_timestamp)?,
                status,
            });
        }
        Ok(convs)
    }

    // ======================================================================
    // Memory entries
    // ======================================================================

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

    /// Count memory entries without embeddings
    pub async fn count_unindexed_entries(&self) -> Result<i64> {
        let row = sqlx::query_as::<_, (i64,)>(
            "SELECT COUNT(*) FROM memory_entries WHERE embedding IS NULL"
        )
        .fetch_one(&self.pool)
        .await?;
        Ok(row.0)
    }

    /// Fetch a batch of memory entries that have no embedding yet
    pub async fn get_unindexed_entries(&self, limit: i64) -> Result<Vec<MemoryEntry>> {
        use sqlx::Row;
        let rows = sqlx::query(
            r#"SELECT id, user_id, content, created_at, updated_at, metadata
               FROM memory_entries WHERE embedding IS NULL
               ORDER BY created_at DESC LIMIT ?"#,
        )
        .bind(limit)
        .fetch_all(&self.pool)
        .await?;

        let entries: Vec<MemoryEntry> = rows
            .iter()
            .map(|row| {
                let id: String = row.get("id");
                let user_id_str: String = row.get("user_id");
                let content: String = row.get("content");
                let created_at_str: String = row.get("created_at");
                let updated_at_str: String = row.get("updated_at");
                let metadata_str: Option<String> = row.get("metadata");

                MemoryEntry {
                    id,
                    user_id: user_id_str.parse().unwrap_or_default(),
                    content,
                    embedding: None,
                    metadata: metadata_str
                        .and_then(|s| serde_json::from_str(&s).ok())
                        .unwrap_or_default(),
                    access_control: Default::default(),
                    created_at: chrono::DateTime::parse_from_rfc3339(&created_at_str)
                        .map(|dt| dt.into())
                        .unwrap_or_else(|_| chrono::Utc::now()),
                    updated_at: chrono::DateTime::parse_from_rfc3339(&updated_at_str)
                        .map(|dt| dt.into())
                        .unwrap_or_else(|_| chrono::Utc::now()),
                    version: 0,
                }
            })
            .collect();

        Ok(entries)
    }

    /// Update the embedding for a specific memory entry
    pub async fn update_embedding(&self, entry_id: &str, embedding_json: &str) -> Result<()> {
        sqlx::query("UPDATE memory_entries SET embedding = ? WHERE id = ?")
            .bind(embedding_json)
            .bind(entry_id)
            .execute(&self.pool)
            .await?;
        Ok(())
    }

    /// Delete stale entries older than `days` with zero access count
    pub async fn cleanup_stale_entries(&self, days: i64) -> Result<i64> {
        let result = sqlx::query(
            r#"DELETE FROM memory_entries
               WHERE updated_at < datetime('now', ? || ' days')
                 AND json_extract(metadata, '$.access_count') = 0"#,
        )
        .bind(-days)
        .execute(&self.pool)
        .await?;
        Ok(result.rows_affected() as i64)
    }

    /// Get recent memory entries (for knowledge inference)
    pub async fn get_recent_entries(&self, limit: i64) -> Result<Vec<serde_json::Value>> {
        use sqlx::Row;
        let rows = sqlx::query(
            r#"SELECT id, user_id, content, entry_type, created_at
               FROM memory_entries
               WHERE created_at > datetime('now', '-1 day')
               ORDER BY created_at DESC
               LIMIT ?"#,
        )
        .bind(limit)
        .fetch_all(&self.pool)
        .await?;

        Ok(rows
            .iter()
            .map(|row| {
                serde_json::json!({
                    "id": row.get::<String, _>("id"),
                    "user_id": row.get::<String, _>("user_id"),
                    "content": row.get::<String, _>("content"),
                    "entry_type": row.get::<String, _>("entry_type"),
                    "created_at": row.get::<String, _>("created_at"),
                })
            })
            .collect())
    }

    /// Prune knowledge graph edges with weight below threshold
    pub async fn prune_knowledge_edges(&self, min_weight: f64) -> Result<i64> {
        let result = sqlx::query("DELETE FROM knowledge_edges WHERE weight < ?")
            .bind(min_weight)
            .execute(&self.pool)
            .await?;
        Ok(result.rows_affected() as i64)
    }

    // ======================================================================
    // Knowledge Graph (FA-003)
    // ======================================================================

    /// Create a knowledge node
    pub async fn save_knowledge_node(
        &self,
        id: &str,
        user_id: &str,
        node_type: &str,
        label: &str,
        properties: &serde_json::Value,
    ) -> Result<()> {
        let now = chrono::Utc::now().to_rfc3339();
        sqlx::query(
            r#"
            INSERT OR REPLACE INTO knowledge_nodes
            (id, user_id, node_type, label, properties, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(id)
        .bind(user_id)
        .bind(node_type)
        .bind(label)
        .bind(serde_json::to_string(properties)?)
        .bind(&now)
        .bind(&now)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    /// Query knowledge nodes
    pub async fn query_knowledge_nodes(
        &self,
        user_id: &str,
        query: Option<&str>,
        node_type: Option<&str>,
        limit: i32,
    ) -> Result<Vec<serde_json::Value>> {
        let (sql, bind_query, bind_type) = match (query, node_type) {
            (Some(q), Some(t)) => (
                r#"SELECT id, node_type, label, properties, created_at, updated_at
                   FROM knowledge_nodes WHERE user_id = ? AND label LIKE ? AND node_type = ?
                   ORDER BY updated_at DESC LIMIT ?"#,
                Some(format!("%{}%", q)),
                Some(t.to_string()),
            ),
            (Some(q), None) => (
                r#"SELECT id, node_type, label, properties, created_at, updated_at
                   FROM knowledge_nodes WHERE user_id = ? AND label LIKE ?
                   ORDER BY updated_at DESC LIMIT ?"#,
                Some(format!("%{}%", q)),
                None,
            ),
            (None, Some(t)) => (
                r#"SELECT id, node_type, label, properties, created_at, updated_at
                   FROM knowledge_nodes WHERE user_id = ? AND node_type = ?
                   ORDER BY updated_at DESC LIMIT ?"#,
                None,
                Some(t.to_string()),
            ),
            (None, None) => (
                r#"SELECT id, node_type, label, properties, created_at, updated_at
                   FROM knowledge_nodes WHERE user_id = ?
                   ORDER BY updated_at DESC LIMIT ?"#,
                None,
                None,
            ),
        };

        // Build query dynamically based on filters present
        let rows: Vec<(String, String, String, String, String, String)> = match (&bind_query, &bind_type) {
            (Some(q), Some(t)) => {
                sqlx::query_as(sql)
                    .bind(user_id).bind(q).bind(t).bind(limit)
                    .fetch_all(&self.pool).await?
            }
            (Some(q), None) => {
                sqlx::query_as(sql)
                    .bind(user_id).bind(q).bind(limit)
                    .fetch_all(&self.pool).await?
            }
            (None, Some(t)) => {
                sqlx::query_as(sql)
                    .bind(user_id).bind(t).bind(limit)
                    .fetch_all(&self.pool).await?
            }
            (None, None) => {
                sqlx::query_as(sql)
                    .bind(user_id).bind(limit)
                    .fetch_all(&self.pool).await?
            }
        };

        let nodes: Vec<serde_json::Value> = rows.into_iter().map(|(id, node_type, label, properties, created_at, updated_at)| {
            serde_json::json!({
                "id": id,
                "node_type": node_type,
                "label": label,
                "properties": serde_json::from_str::<serde_json::Value>(&properties).unwrap_or_default(),
                "created_at": created_at,
                "updated_at": updated_at,
            })
        }).collect();

        Ok(nodes)
    }

    /// Create a knowledge edge
    pub async fn save_knowledge_edge(
        &self,
        id: &str,
        source_id: &str,
        target_id: &str,
        relationship: &str,
        weight: f64,
    ) -> Result<()> {
        let now = chrono::Utc::now().to_rfc3339();
        sqlx::query(
            r#"
            INSERT OR REPLACE INTO knowledge_edges
            (id, source_id, target_id, relationship, weight, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(id)
        .bind(source_id)
        .bind(target_id)
        .bind(relationship)
        .bind(weight)
        .bind(now)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    /// Query knowledge edges for a set of node IDs
    pub async fn query_knowledge_edges(&self, node_ids: &[String]) -> Result<Vec<serde_json::Value>> {
        if node_ids.is_empty() {
            return Ok(Vec::new());
        }
        let placeholders: Vec<&str> = node_ids.iter().map(|_| "?").collect();
        let in_clause = placeholders.join(",");
        let sql = format!(
            r#"SELECT id, source_id, target_id, relationship, weight, created_at
               FROM knowledge_edges
               WHERE source_id IN ({in_clause}) OR target_id IN ({in_clause})"#,
        );

        let mut query = sqlx::query_as::<_, (String, String, String, String, f64, String)>(&sql);
        // Bind source_id IN params
        for nid in node_ids {
            query = query.bind(nid);
        }
        // Bind target_id IN params
        for nid in node_ids {
            query = query.bind(nid);
        }
        let rows = query.fetch_all(&self.pool).await?;

        let edges: Vec<serde_json::Value> = rows.into_iter().map(|(id, source_id, target_id, relationship, weight, created_at)| {
            serde_json::json!({
                "id": id,
                "source_id": source_id,
                "target_id": target_id,
                "relationship": relationship,
                "weight": weight,
                "created_at": created_at,
            })
        }).collect();

        Ok(edges)
    }

    // ======================================================================
    // Health Data (FA-008)
    // ======================================================================

    /// Save a health data entry
    pub async fn save_health_data(
        &self,
        id: &str,
        user_id: &str,
        source: &str,
        data_type: &str,
        value: f64,
        unit: &str,
        confidence: f64,
    ) -> Result<()> {
        let now = chrono::Utc::now().to_rfc3339();
        sqlx::query(
            r#"
            INSERT INTO health_data
            (id, user_id, source, timestamp, data_type, value, unit, confidence, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, '{}')
            "#,
        )
        .bind(id)
        .bind(user_id)
        .bind(source)
        .bind(&now)
        .bind(data_type)
        .bind(value)
        .bind(unit)
        .bind(confidence)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    /// List health data entries
    pub async fn list_health_data(
        &self,
        user_id: &str,
        data_type: Option<&str>,
        from: Option<&str>,
        to: Option<&str>,
        limit: i32,
    ) -> Result<Vec<serde_json::Value>> {
        let mut sql = String::from(
            "SELECT id, source, timestamp, data_type, value, unit, confidence FROM health_data WHERE user_id = ?"
        );
        let mut binds: Vec<String> = vec![user_id.to_string()];

        if let Some(dt) = data_type {
            sql.push_str(" AND data_type = ?");
            binds.push(dt.to_string());
        }
        if let Some(f) = from {
            sql.push_str(" AND timestamp >= ?");
            binds.push(f.to_string());
        }
        if let Some(t) = to {
            sql.push_str(" AND timestamp <= ?");
            binds.push(t.to_string());
        }
        sql.push_str(" ORDER BY timestamp DESC LIMIT ?");
        binds.push(limit.to_string());

        let mut query = sqlx::query_as::<_, (String, String, String, String, f64, String, f64)>(&sql);
        for b in &binds {
            query = query.bind(b);
        }

        let rows = query.fetch_all(&self.pool).await?;
        let entries: Vec<serde_json::Value> = rows.into_iter().map(|(id, source, timestamp, data_type, value, unit, confidence)| {
            serde_json::json!({
                "id": id,
                "source": source,
                "timestamp": timestamp,
                "data_type": data_type,
                "value": value,
                "unit": unit,
                "confidence": confidence,
            })
        }).collect();

        Ok(entries)
    }

    // ======================================================================
    // Action Plans (FA-002)
    // ======================================================================

    /// Save an action plan
    pub async fn save_action_plan(
        &self,
        id: &str,
        user_id: &str,
        trigger: &str,
        status: &str,
        steps: &serde_json::Value,
        requires_approval: bool,
    ) -> Result<()> {
        let now = chrono::Utc::now().to_rfc3339();
        sqlx::query(
            r#"
            INSERT OR REPLACE INTO action_plans
            (id, user_id, trigger, status, steps, created_at, requires_approval, approval_granted)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            "#,
        )
        .bind(id)
        .bind(user_id)
        .bind(trigger)
        .bind(status)
        .bind(serde_json::to_string(steps)?)
        .bind(now)
        .bind(requires_approval as i32)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    /// List action plans
    pub async fn list_action_plans(
        &self,
        user_id: &str,
        status: Option<&str>,
        limit: i32,
    ) -> Result<Vec<serde_json::Value>> {
        let (sql, has_status) = if status.is_some() {
            (r#"SELECT id, trigger, status, steps, created_at, completed_at, requires_approval, approval_granted
                FROM action_plans WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC LIMIT ?"#, true)
        } else {
            (r#"SELECT id, trigger, status, steps, created_at, completed_at, requires_approval, approval_granted
                FROM action_plans WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?"#, false)
        };

        let rows: Vec<(String, String, String, String, String, Option<String>, i32, i32)> = if has_status {
            sqlx::query_as(sql)
                .bind(user_id).bind(status.unwrap()).bind(limit)
                .fetch_all(&self.pool).await?
        } else {
            sqlx::query_as(sql)
                .bind(user_id).bind(limit)
                .fetch_all(&self.pool).await?
        };

        let plans: Vec<serde_json::Value> = rows.into_iter().map(|(id, trigger, status, steps, created_at, completed_at, requires_approval, approval_granted)| {
            serde_json::json!({
                "id": id,
                "trigger": trigger,
                "status": status,
                "steps": serde_json::from_str::<serde_json::Value>(&steps).unwrap_or_default(),
                "created_at": created_at,
                "completed_at": completed_at,
                "requires_approval": requires_approval != 0,
                "approval_granted": approval_granted != 0,
            })
        }).collect();

        Ok(plans)
    }

    /// Update action plan status
    pub async fn update_action_plan_status(
        &self,
        id: &str,
        status: &str,
        approval_granted: Option<bool>,
    ) -> Result<bool> {
        let mut sql = String::from("UPDATE action_plans SET status = ?");
        let mut binds: Vec<String> = vec![status.to_string()];

        if let Some(approved) = approval_granted {
            sql.push_str(", approval_granted = ?");
            binds.push(if approved { "1".into() } else { "0".into() });
        }
        if status == "completed" {
            sql.push_str(", completed_at = ?");
            binds.push(chrono::Utc::now().to_rfc3339());
        }
        sql.push_str(" WHERE id = ?");
        binds.push(id.to_string());

        let mut query = sqlx::query(&sql);
        for b in &binds {
            query = query.bind(b);
        }
        let result = query.execute(&self.pool).await?;
        Ok(result.rows_affected() > 0)
    }

    /// Get a single action plan by ID
    pub async fn get_action_plan(&self, id: &str) -> Result<Option<serde_json::Value>> {
        let row = sqlx::query_as::<_, (String, String, String, String, String, String, Option<String>, i32, i32)>(
            r#"SELECT id, user_id, trigger, status, steps, created_at, completed_at, requires_approval, approval_granted
               FROM action_plans WHERE id = ?"#,
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?;

        Ok(row.map(|(id, _user_id, trigger, status, steps, created_at, completed_at, requires_approval, approval_granted)| {
            serde_json::json!({
                "id": id,
                "trigger": trigger,
                "status": status,
                "steps": serde_json::from_str::<serde_json::Value>(&steps).unwrap_or_default(),
                "created_at": created_at,
                "completed_at": completed_at,
                "requires_approval": requires_approval != 0,
                "approval_granted": approval_granted != 0,
            })
        }))
    }

    // ======================================================================
    // Plugins
    // ======================================================================

    /// Save a plugin record
    pub async fn save_plugin(
        &self,
        id: &str,
        name: &str,
        version: &str,
        description: Option<&str>,
        enabled: bool,
    ) -> Result<()> {
        let now = chrono::Utc::now().to_rfc3339();
        sqlx::query(
            r#"
            INSERT OR REPLACE INTO plugins
            (id, name, version, description, author, capabilities, permissions, entry_points, compatibility, installed_at, enabled)
            VALUES (?, ?, ?, ?, '{}', '{}', '{}', '{}', '{}', ?, ?)
            "#,
        )
        .bind(id)
        .bind(name)
        .bind(version)
        .bind(description)
        .bind(now)
        .bind(enabled as i32)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    /// List all plugins
    pub async fn list_plugins(&self) -> Result<Vec<serde_json::Value>> {
        let rows = sqlx::query_as::<_, (String, String, String, Option<String>, i32)>(
            "SELECT id, name, version, description, enabled FROM plugins ORDER BY name",
        )
        .fetch_all(&self.pool)
        .await?;

        let plugins: Vec<serde_json::Value> = rows.into_iter().map(|(id, name, version, description, enabled)| {
            serde_json::json!({
                "id": id,
                "name": name,
                "version": version,
                "description": description,
                "enabled": enabled != 0,
            })
        }).collect();

        Ok(plugins)
    }

    /// Toggle plugin enabled state
    pub async fn toggle_plugin(&self, id: &str) -> Result<bool> {
        let result = sqlx::query(
            "UPDATE plugins SET enabled = CASE WHEN enabled = 1 THEN 0 ELSE 1 END WHERE id = ?",
        )
        .bind(id)
        .execute(&self.pool)
        .await?;
        Ok(result.rows_affected() > 0)
    }

    /// Delete a plugin
    pub async fn delete_plugin(&self, id: &str) -> Result<bool> {
        let result = sqlx::query("DELETE FROM plugins WHERE id = ?")
            .bind(id)
            .execute(&self.pool)
            .await?;
        Ok(result.rows_affected() > 0)
    }

    // ======================================================================
    // Notifications (FA-012)
    // ======================================================================

    /// Save a notification to the database
    pub async fn save_notification(&self, notif: &crate::notifications::Notification) -> Result<()> {
        sqlx::query(
            r#"
            INSERT OR REPLACE INTO notifications
            (id, user_id, device_id, notification_type, title, body, priority, category,
             icon, data, delivery_time, expiration, status, personalization, created_at,
             read_at, read, dismissed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(notif.id.to_string())
        .bind(notif.user_id.map(|u| u.to_string()))
        .bind(notif.device_id.map(|d| d.to_string()))
        .bind(serde_json::to_string(&notif.notification_type)?.trim_matches('"'))
        .bind(&notif.title)
        .bind(&notif.body)
        .bind(serde_json::to_string(&notif.priority)?.trim_matches('"'))
        .bind(serde_json::to_string(&notif.category)?.trim_matches('"'))
        .bind(&notif.icon)
        .bind(notif.data.as_ref().map(|d| serde_json::to_string(d).unwrap_or_default()))
        .bind(notif.delivery_time.map(|dt| dt.to_rfc3339()))
        .bind(notif.expiration.map(|dt| dt.to_rfc3339()))
        .bind(serde_json::to_string(&notif.status)?.trim_matches('"'))
        .bind(notif.personalization.as_ref().map(|p| serde_json::to_string(p).unwrap_or_default()))
        .bind(notif.created_at.to_rfc3339())
        .bind(notif.read_at.map(|dt| dt.to_rfc3339()))
        .bind(notif.read as i32)
        .bind(notif.dismissed as i32)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    /// Load all active notifications from the database
    pub async fn load_notifications(&self) -> Result<Vec<crate::notifications::Notification>> {
        use sqlx::Row;

        let rows = sqlx::query(
            r#"SELECT id, user_id, device_id, notification_type, title, body, priority, category,
                      icon, data, delivery_time, expiration, status, personalization, created_at,
                      read_at, read, dismissed
               FROM notifications
               WHERE dismissed = 0
               ORDER BY created_at DESC
               LIMIT 200"#,
        )
        .fetch_all(&self.pool)
        .await?;

        let mut notifications = Vec::new();
        for row in rows {
            let id_str: String = row.get("id");
            let user_id_str: Option<String> = row.get("user_id");
            let device_id_str: Option<String> = row.get("device_id");
            let ntype_str: String = row.get("notification_type");
            let title: String = row.get("title");
            let body: String = row.get("body");
            let priority_str: String = row.get("priority");
            let category_str: String = row.get("category");
            let icon: Option<String> = row.get("icon");
            let data_str: Option<String> = row.get("data");
            let delivery_time_str: Option<String> = row.get("delivery_time");
            let expiration_str: Option<String> = row.get("expiration");
            let status_str: String = row.get("status");
            let personalization_str: Option<String> = row.get("personalization");
            let created_at_str: String = row.get("created_at");
            let read_at_str: Option<String> = row.get("read_at");
            let read_val: i32 = row.get("read");
            let dismissed_val: i32 = row.get("dismissed");

            let notif = crate::notifications::Notification {
                id: id_str.parse().unwrap_or_default(),
                user_id: user_id_str.and_then(|s: String| s.parse().ok()),
                device_id: device_id_str.and_then(|s: String| s.parse().ok()),
                notification_type: serde_json::from_str(&format!("\"{}\"", ntype_str)).unwrap_or(crate::notifications::NotificationType::System),
                title,
                body,
                priority: serde_json::from_str(&format!("\"{}\"", priority_str)).unwrap_or(crate::notifications::NotificationPriority::Medium),
                category: serde_json::from_str(&format!("\"{}\"", category_str)).unwrap_or(crate::notifications::NotificationCategory::System),
                icon,
                data: data_str.and_then(|s: String| serde_json::from_str(&s).ok()),
                delivery_time: delivery_time_str.and_then(|s: String| chrono::DateTime::parse_from_rfc3339(&s).ok().map(|dt| dt.into())),
                expiration: expiration_str.and_then(|s: String| chrono::DateTime::parse_from_rfc3339(&s).ok().map(|dt| dt.into())),
                status: serde_json::from_str(&format!("\"{}\"", status_str)).unwrap_or(crate::notifications::NotificationStatus::Pending),
                personalization: personalization_str.and_then(|s: String| serde_json::from_str(&s).ok()),
                created_at: chrono::DateTime::parse_from_rfc3339(&created_at_str).map(|dt| dt.into()).unwrap_or_else(|_| chrono::Utc::now()),
                read_at: read_at_str.and_then(|s: String| chrono::DateTime::parse_from_rfc3339(&s).ok().map(|dt| dt.into())),
                read: read_val != 0,
                dismissed: dismissed_val != 0,
            };
            notifications.push(notif);
        }

        Ok(notifications)
    }

    /// Delete expired notifications from the database
    pub async fn delete_expired_notifications(&self) -> Result<u64> {
        let now = chrono::Utc::now().to_rfc3339();
        let result = sqlx::query(
            "DELETE FROM notifications WHERE expiration IS NOT NULL AND expiration < ?"
        )
        .bind(now)
        .execute(&self.pool)
        .await?;
        Ok(result.rows_affected())
    }

    // ======================================================================
    // Subscriptions
    // ======================================================================

    /// Save a subscription
    pub async fn save_subscription(&self, subscription: &crate::models::subscription::Subscription) -> Result<()> {
        let now = chrono::Utc::now().to_rfc3339();
        sqlx::query(
            r#"
            INSERT OR REPLACE INTO subscriptions
            (id, user_id, tier, status, provider, provider_subscription_id, start_date, end_date, auto_renew, features, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(subscription.id.to_string())
        .bind(subscription.user_id.to_string())
        .bind(serde_json::to_string(&subscription.tier)?.trim_matches('"'))
        .bind(serde_json::to_string(&subscription.status)?.trim_matches('"'))
        .bind(serde_json::to_string(&subscription.provider)?.trim_matches('"'))
        .bind(&subscription.provider_subscription_id)
        .bind(subscription.start_date.to_rfc3339())
        .bind(subscription.end_date.to_rfc3339())
        .bind(subscription.auto_renew as i32)
        .bind(serde_json::to_string(&subscription.features)?)
        .bind(&now)
        .bind(&now)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    /// Get subscription for a user
    pub async fn get_subscription(&self, user_id: &str) -> Result<Option<crate::models::subscription::Subscription>> {
        use sqlx::Row;
        let row = sqlx::query(
            r#"SELECT id, user_id, tier, status, provider, provider_subscription_id, start_date, end_date, auto_renew, features
               FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1"#,
        )
        .bind(user_id)
        .fetch_optional(&self.pool)
        .await?;

        match row {
            Some(row) => {
                let id: String = row.get("id");
                let user_id: String = row.get("user_id");
                let tier_str: String = row.get("tier");
                let status_str: String = row.get("status");
                let provider_str: String = row.get("provider");
                let provider_subscription_id: Option<String> = row.get("provider_subscription_id");
                let start_date_str: String = row.get("start_date");
                let end_date_str: String = row.get("end_date");
                let auto_renew_val: i32 = row.get("auto_renew");
                let features_str: String = row.get("features");

                Ok(Some(crate::models::subscription::Subscription {
                    id: id.parse().unwrap_or_default(),
                    user_id: user_id.parse().unwrap_or_default(),
                    tier: serde_json::from_str(&format!("\"{}\"", tier_str)).unwrap_or(crate::models::subscription::SubscriptionTier::Freemium),
                    status: serde_json::from_str(&format!("\"{}\"", status_str)).unwrap_or(crate::models::subscription::SubscriptionStatus::Active),
                    provider: serde_json::from_str(&format!("\"{}\"", provider_str)).unwrap_or(crate::models::subscription::PaymentProvider::Manual),
                    provider_subscription_id,
                    start_date: chrono::DateTime::parse_from_rfc3339(&start_date_str).map(|dt| dt.into()).unwrap_or_else(|_| chrono::Utc::now()),
                    end_date: chrono::DateTime::parse_from_rfc3339(&end_date_str).map(|dt| dt.into()).unwrap_or_else(|_| chrono::Utc::now()),
                    auto_renew: auto_renew_val != 0,
                    features: serde_json::from_str(&features_str).unwrap_or_default(),
                }))
            }
            None => Ok(None),
        }
    }

    /// Update subscription tier
    pub async fn update_subscription_tier(&self, user_id: &str, tier: &str) -> Result<bool> {
        let now = chrono::Utc::now().to_rfc3339();
        let result = sqlx::query(
            "UPDATE subscriptions SET tier = ?, updated_at = ? WHERE user_id = ?",
        )
        .bind(tier)
        .bind(&now)
        .bind(user_id)
        .execute(&self.pool)
        .await?;
        Ok(result.rows_affected() > 0)
    }

    // ======================================================================
    // Smart Home Devices (FA-006)
    // ======================================================================

    /// Save a smart device
    pub async fn save_smart_device(&self, device: &crate::models::smart_home::SmartDevice) -> Result<()> {
        let now = chrono::Utc::now().to_rfc3339();
        let device_type_str = serde_json::to_string(&device.device_type)?.trim_matches('"').to_string();
        
        sqlx::query(
            r#"
            INSERT OR REPLACE INTO smart_devices
            (id, user_id, name, device_type, protocol, is_online, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(device.id.to_string())
        .bind(device.user_id.to_string())
        .bind(&device.name)
        .bind(&device_type_str)
        .bind(&device.protocol)
        .bind(device.is_online as i32)
        .bind(serde_json::to_string(&device.state)?)
        .bind(&now)
        .bind(&now)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    /// List smart devices for a user
    pub async fn list_smart_devices(&self, user_id: &str) -> Result<Vec<crate::models::smart_home::SmartDevice>> {
        use sqlx::Row;
        let rows = sqlx::query(
            r#"SELECT id, user_id, name, device_type, protocol, is_online, state FROM smart_devices WHERE user_id = ?"#,
        )
        .bind(user_id)
        .fetch_all(&self.pool)
        .await?;

        let devices: Vec<crate::models::smart_home::SmartDevice> = rows
            .iter()
            .map(|row| {
                let id: String = row.get("id");
                let user_id: String = row.get("user_id");
                let name: String = row.get("name");
                let device_type_str: String = row.get("device_type");
                let protocol: String = row.get("protocol");
                let is_online_val: i32 = row.get("is_online");
                let state_str: String = row.get("state");

                crate::models::smart_home::SmartDevice {
                    id: id.parse().unwrap_or_default(),
                    user_id: user_id.parse().unwrap_or_default(),
                    name,
                    device_type: serde_json::from_str(&format!("\"{}\"", device_type_str)).unwrap_or(crate::models::smart_home::DeviceType::Unknown("unknown".to_string())),
                    protocol,
                    is_online: is_online_val != 0,
                    state: serde_json::from_str(&state_str).unwrap_or_default(),
                }
            })
            .collect();

        Ok(devices)
    }

    /// Update smart device state
    pub async fn update_smart_device_state(&self, device_id: &str, state: &serde_json::Value) -> Result<bool> {
        let now = chrono::Utc::now().to_rfc3339();
        let result = sqlx::query(
            "UPDATE smart_devices SET state = ?, updated_at = ? WHERE id = ?",
        )
        .bind(serde_json::to_string(state)?)
        .bind(&now)
        .bind(device_id)
        .execute(&self.pool)
        .await?;
        Ok(result.rows_affected() > 0)
    }

    /// Delete a smart device
    pub async fn delete_smart_device(&self, device_id: &str) -> Result<bool> {
        let result = sqlx::query("DELETE FROM smart_devices WHERE id = ?")
            .bind(device_id)
            .execute(&self.pool)
            .await?;
        Ok(result.rows_affected() > 0)
    }

    // ======================================================================
    // Smart Home Scenes (FA-006)
    // ======================================================================

    /// Save a smart scene
    pub async fn save_smart_scene(&self, scene: &crate::models::smart_home::HomeScene) -> Result<()> {
        let now = chrono::Utc::now().to_rfc3339();
        sqlx::query(
            r#"
            INSERT OR REPLACE INTO smart_scenes
            (id, user_id, name, description, actions, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(scene.id.to_string())
        .bind(scene.user_id.to_string())
        .bind(&scene.name)
        .bind(&scene.description)
        .bind(serde_json::to_string(&scene.actions)?)
        .bind(&now)
        .bind(&now)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    /// List smart scenes for a user
    pub async fn list_smart_scenes(&self, user_id: &str) -> Result<Vec<crate::models::smart_home::HomeScene>> {
        use sqlx::Row;
        let rows = sqlx::query(
            r#"SELECT id, user_id, name, description, actions FROM smart_scenes WHERE user_id = ?"#,
        )
        .bind(user_id)
        .fetch_all(&self.pool)
        .await?;

        let scenes: Vec<crate::models::smart_home::HomeScene> = rows
            .iter()
            .map(|row| {
                let id: String = row.get("id");
                let user_id: String = row.get("user_id");
                let name: String = row.get("name");
                let description: Option<String> = row.get("description");
                let actions_str: String = row.get("actions");

                crate::models::smart_home::HomeScene {
                    id: id.parse().unwrap_or_default(),
                    user_id: user_id.parse().unwrap_or_default(),
                    name,
                    description,
                    actions: serde_json::from_str(&actions_str).unwrap_or_default(),
                }
            })
            .collect();

        Ok(scenes)
    }

    /// Delete a smart scene
    pub async fn delete_smart_scene(&self, scene_id: &str) -> Result<bool> {
        let result = sqlx::query("DELETE FROM smart_scenes WHERE id = ?")
            .bind(scene_id)
            .execute(&self.pool)
            .await?;
        Ok(result.rows_affected() > 0)
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
    async fn test_conversation_list() {
        let store = MemoryStore::in_memory().await.unwrap();

        let mut conv1 = Conversation::default();
        conv1.add_message(Message::user("First"));
        store.save_conversation(&conv1).await.unwrap();

        let mut conv2 = Conversation::default();
        conv2.add_message(Message::user("Second"));
        store.save_conversation(&conv2).await.unwrap();

        let all = store.list_all_conversations(50).await.unwrap();
        assert_eq!(all.len(), 2);
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

    #[tokio::test]
    async fn test_knowledge_graph_crud() {
        let store = MemoryStore::in_memory().await.unwrap();
        let user_id = Uuid::new_v4().to_string();
        let node_id1 = Uuid::new_v4().to_string();
        let node_id2 = Uuid::new_v4().to_string();

        // Create nodes
        store.save_knowledge_node(&node_id1, &user_id, "concept", "Rust", &serde_json::json!({"lang": true})).await.unwrap();
        store.save_knowledge_node(&node_id2, &user_id, "concept", "WebAssembly", &serde_json::json!({})).await.unwrap();

        // Query nodes
        let nodes = store.query_knowledge_nodes(&user_id, None, None, 10).await.unwrap();
        assert_eq!(nodes.len(), 2);

        let filtered = store.query_knowledge_nodes(&user_id, Some("Rust"), None, 10).await.unwrap();
        assert_eq!(filtered.len(), 1);

        // Create edge
        let edge_id = Uuid::new_v4().to_string();
        store.save_knowledge_edge(&edge_id, &node_id1, &node_id2, "compiles_to", 1.0).await.unwrap();

        // Query edges
        let edges = store.query_knowledge_edges(&[node_id1.clone()]).await.unwrap();
        assert_eq!(edges.len(), 1);
    }

    #[tokio::test]
    async fn test_health_data_crud() {
        let store = MemoryStore::in_memory().await.unwrap();
        let user_id = Uuid::new_v4().to_string();
        let id = Uuid::new_v4().to_string();

        store.save_health_data(&id, &user_id, "wearable", "heart_rate", 72.0, "bpm", 0.95).await.unwrap();

        let entries = store.list_health_data(&user_id, Some("heart_rate"), None, None, 10).await.unwrap();
        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0]["value"], 72.0);
    }

    #[tokio::test]
    async fn test_action_plan_crud() {
        let store = MemoryStore::in_memory().await.unwrap();
        let user_id = Uuid::new_v4().to_string();
        let plan_id = Uuid::new_v4().to_string();

        store.save_action_plan(
            &plan_id, &user_id, "Book flight", "pending",
            &serde_json::json!([{"action": "search_flights"}]),
            true,
        ).await.unwrap();

        let plans = store.list_action_plans(&user_id, None, 10).await.unwrap();
        assert_eq!(plans.len(), 1);

        // Approve
        store.update_action_plan_status(&plan_id, "approved", Some(true)).await.unwrap();

        let plan = store.get_action_plan(&plan_id).await.unwrap().unwrap();
        assert_eq!(plan["status"], "approved");
    }

    #[tokio::test]
    async fn test_plugin_crud() {
        let store = MemoryStore::in_memory().await.unwrap();
        let id = Uuid::new_v4().to_string();

        store.save_plugin(&id, "weather", "1.0.0", Some("Weather plugin"), true).await.unwrap();

        let plugins = store.list_plugins().await.unwrap();
        assert_eq!(plugins.len(), 1);
        assert_eq!(plugins[0]["enabled"], true);

        // Toggle
        store.toggle_plugin(&id).await.unwrap();
        let plugins = store.list_plugins().await.unwrap();
        assert_eq!(plugins[0]["enabled"], false);

        // Delete
        store.delete_plugin(&id).await.unwrap();
        let plugins = store.list_plugins().await.unwrap();
        assert_eq!(plugins.len(), 0);
    }
}
