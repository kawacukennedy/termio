//! Vector store for semantic search
//!
//! SQLite-based vector storage with cosine similarity search.
//!
//! This is the second tier in TERMIO's three-tier memory architecture:
//! - Provides semantic similarity search over embeddings
//! - Enables finding related memories, conversations, and knowledge
//!
//! ## How it works
//!
//! 1. Text content is converted to embeddings using an external ML model
//! 2. Embeddings are stored as byte arrays in SQLite (f32 -> little-endian bytes)
//! 3. Search computes cosine similarity between query and stored vectors
//! 4. Results are sorted by similarity and filtered by threshold
//!
//! ## Usage
//!
//! ```rust
//! let store = VectorStore::new(pool, 384); // 384-dimensional embeddings
//! store.initialize().await?;
//!
//! // Insert
//! store.insert(&VectorEntry {
//!     id: "mem_1".into(),
//!     content: "User prefers dark mode".into(),
//!     embedding: vec![0.1, -0.2, ...], // 384 dims
//!     metadata: json!({"type": "preference"}),
//! }).await?;
//!
//! // Search
//! let results = store.search(&query_embedding, 5, 0.7).await?;
//! for (entry, score) in results { ... }
//! ```

use serde::{Deserialize, Serialize};
use sqlx::{Pool, Sqlite};

use crate::error::Result;

/// A vector entry in the store
///
/// Represents a piece of content with its embedding vector.
/// Used for semantic search across memories and knowledge.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VectorEntry {
    /// Unique identifier for this entry
    pub id: String,
    /// Original text content
    pub content: String,
    /// Embedding vector (typically 384-1536 dimensions)
    pub embedding: Vec<f32>,
    /// Additional metadata (source, timestamp, tags, etc.)
    pub metadata: serde_json::Value,
}

/// Vector store for semantic search
///
/// Uses cosine similarity to find related content.
/// In production, consider replacing with specialized vector databases
/// (Milvus, Pinecone, Qdrant) for better performance at scale.
pub struct VectorStore {
    pool: Pool<Sqlite>,
    /// Embedding dimensions (must match the embedding model)
    dimensions: usize,
}

impl VectorStore {
    /// Create a new vector store
    ///
    /// The `dimensions` parameter must match your embedding model's output size:
    /// - OpenAI ada-002: 1536
    /// - sentence-transformers/all-MiniLM-L6-v2: 384
    pub fn new(pool: Pool<Sqlite>, dimensions: usize) -> Self {
        Self { pool, dimensions }
    }

    /// Get the embedding dimensions
    pub fn dimensions(&self) -> usize {
        self.dimensions
    }

    fn pool(&self) -> &Pool<Sqlite> {
        &self.pool
    }

    /// Initialize the vector store tables
    ///
    /// Creates the vectors table with content, embedding, and metadata columns.
    /// Embeddings are stored as BLOB (raw bytes) for efficiency.
    pub async fn initialize(&self) -> Result<()> {
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS vectors (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_vectors_created 
            ON vectors(created_at);
            "#,
        )
        .execute(self.pool())
        .await?;

        Ok(())
    }

    /// Insert a vector entry
    pub async fn insert(&self, entry: &VectorEntry) -> Result<()> {
        let embedding_bytes = self.embedding_to_bytes(&entry.embedding);
        let metadata_json = serde_json::to_string(&entry.metadata)?;

        sqlx::query(
            r#"
            INSERT OR REPLACE INTO vectors (id, content, embedding, metadata)
            VALUES (?, ?, ?, ?)
            "#,
        )
        .bind(&entry.id)
        .bind(&entry.content)
        .bind(&embedding_bytes)
        .bind(&metadata_json)
        .execute(self.pool())
        .await?;

        Ok(())
    }

    /// Search for similar vectors
    ///
    /// Computes cosine similarity between the query embedding and all stored vectors.
    /// Returns entries with similarity above the threshold, sorted by score.
    ///
    /// # Arguments
    /// * `query_embedding` - The embedding vector to search with
    /// * `limit` - Maximum number of results to return
    /// * `threshold` - Minimum similarity score (0.0 to 1.0)
    ///
    /// # Performance Note
    /// This is a brute-force O(n) scan. For large datasets (>10k vectors),
    /// consider using approximate nearest neighbor (ANN) indexes or a
    /// specialized vector database.
    pub async fn search(
        &self,
        query_embedding: &[f32],
        limit: usize,
        threshold: f32,
    ) -> Result<Vec<(VectorEntry, f32)>> {
        let rows = sqlx::query_as::<_, (String, String, Vec<u8>, String)>(
            "SELECT id, content, embedding, metadata FROM vectors"
        )
        .fetch_all(self.pool())
        .await?;

        let mut results: Vec<(VectorEntry, f32)> = Vec::new();

        for (id, content, embedding_bytes, metadata_json) in rows {
            let embedding = self.bytes_to_embedding(&embedding_bytes);
            let similarity = cosine_similarity_impl(query_embedding, &embedding);

            if similarity >= threshold {
                let entry = VectorEntry {
                    id,
                    content,
                    embedding,
                    metadata: serde_json::from_str(&metadata_json)?,
                };
                results.push((entry, similarity));
            }
        }

        results.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        results.truncate(limit);

        Ok(results)
    }

    /// Delete a vector by ID
    pub async fn delete(&self, id: &str) -> Result<bool> {
        let result = sqlx::query("DELETE FROM vectors WHERE id = ?")
            .bind(id)
            .execute(self.pool())
            .await?;

        Ok(result.rows_affected() > 0)
    }

    /// Get a vector by ID
    pub async fn get(&self, id: &str) -> Result<Option<VectorEntry>> {
        let row = sqlx::query_as::<_, (String, String, Vec<u8>, String)>(
            "SELECT id, content, embedding, metadata FROM vectors WHERE id = ?"
        )
        .bind(id)
        .fetch_optional(self.pool())
        .await?;

        match row {
            Some((id, content, embedding_bytes, metadata_json)) => {
                Ok(Some(VectorEntry {
                    id,
                    content,
                    embedding: bytes_to_embedding(&embedding_bytes),
                    metadata: serde_json::from_str(&metadata_json)?,
                }))
            }
            None => Ok(None),
        }
    }

    fn embedding_to_bytes(&self, embedding: &[f32]) -> Vec<u8> {
        embedding.iter().flat_map(|f| f.to_le_bytes()).collect()
    }

    fn bytes_to_embedding(&self, bytes: &[u8]) -> Vec<f32> {
        bytes
            .chunks(4)
            .map(|chunk| f32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
            .collect()
    }
}

/// Calculate cosine similarity between two vectors
///
/// Cosine similarity measures the angle between vectors:
/// - 1.0 = identical direction (most similar)
/// - 0.0 = orthogonal (no similarity)
/// - -1.0 = opposite direction
///
/// Formula: (a · b) / (||a|| * ||b||)
pub fn cosine_similarity_impl(a: &[f32], b: &[f32]) -> f32 {
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let mag_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let mag_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();

    if mag_a == 0.0 || mag_b == 0.0 {
        return 0.0;
    }

    dot / (mag_a * mag_b)
}

/// Convert embedding to bytes
pub fn embedding_to_bytes(embedding: &[f32]) -> Vec<u8> {
    embedding.iter().flat_map(|f| f.to_le_bytes()).collect()
}

/// Convert bytes to embedding
pub fn bytes_to_embedding(bytes: &[u8]) -> Vec<f32> {
    bytes
        .chunks(4)
        .map(|chunk| f32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cosine_similarity() {
        let a = vec![1.0, 0.0, 0.0];
        let b = vec![1.0, 0.0, 0.0];
        assert!((cosine_similarity_impl(&a, &b) - 1.0).abs() < 0.001);

        let c = vec![0.0, 1.0, 0.0];
        assert!((cosine_similarity_impl(&a, &c) - 0.0).abs() < 0.001);
    }

    #[test]
    fn test_embedding_serialization() {
        let embedding = vec![1.5, -2.0, 3.14159];
        let bytes = embedding_to_bytes(&embedding);
        let restored = bytes_to_embedding(&bytes);

        assert_eq!(embedding.len(), restored.len());
        for (a, b) in embedding.iter().zip(restored.iter()) {
            assert!((a - b).abs() < 0.0001);
        }
    }
}
