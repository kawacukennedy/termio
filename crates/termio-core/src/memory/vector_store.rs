//! Vector store for semantic search
//!
//! SQLite-based vector storage with cosine similarity search.

use serde::{Deserialize, Serialize};
use sqlx::{Pool, Sqlite};

use crate::error::Result;

/// A vector entry in the store
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VectorEntry {
    pub id: String,
    pub content: String,
    pub embedding: Vec<f32>,
    pub metadata: serde_json::Value,
}

/// Vector store for semantic search
pub struct VectorStore {
    pool: Pool<Sqlite>,
    dimensions: usize,
}

impl VectorStore {
    /// Create a new vector store
    pub fn new(pool: Pool<Sqlite>, dimensions: usize) -> Self {
        Self { pool, dimensions }
    }

    /// Get the dimensions
    pub fn dimensions(&self) -> usize {
        self.dimensions
    }

    fn pool(&self) -> &Pool<Sqlite> {
        &self.pool
    }

    /// Initialize the vector store tables
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
