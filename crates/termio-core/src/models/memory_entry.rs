//! Memory entry model

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Source of a memory entry
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum MemorySource {
    /// From a conversation
    Conversation,
    /// From an uploaded document
    Document,
    /// From a plugin
    Plugin,
    /// Manually created
    Manual,
}

/// Sharing policy for memory entries
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SharingPolicy {
    /// Only accessible on this device
    Private,
    /// Shared across user's devices
    SharedDevices,
    /// Shared with specific users
    SharedUsers,
}

/// Metadata for a memory entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryMetadata {
    /// Source of the memory
    pub source: MemorySource,

    /// Importance score (0-1)
    pub importance_score: f32,

    /// How often this memory is accessed
    pub access_frequency: u32,

    /// When this memory was last accessed
    pub last_accessed: DateTime<Utc>,

    /// Tags for categorization
    pub tags: Vec<String>,
}

impl Default for MemoryMetadata {
    fn default() -> Self {
        Self {
            source: MemorySource::Manual,
            importance_score: 0.5,
            access_frequency: 0,
            last_accessed: Utc::now(),
            tags: Vec::new(),
        }
    }
}

/// Access control for a memory entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccessControl {
    /// Required capabilities to access
    pub capabilities_required: Vec<String>,

    /// Encryption key ID
    pub encryption_key_id: Option<String>,

    /// Sharing policy
    pub sharing_policy: SharingPolicy,
}

impl Default for AccessControl {
    fn default() -> Self {
        Self {
            capabilities_required: Vec::new(),
            encryption_key_id: None,
            sharing_policy: SharingPolicy::Private,
        }
    }
}

/// A semantic memory entry with optional embeddings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryEntry {
    /// Unique ID (ULID for time-ordering)
    pub id: String,

    /// User who owns this memory
    pub user_id: Uuid,

    /// Text content
    pub content: String,

    /// Optional embedding vector (768 dimensions)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub embedding: Option<Vec<f32>>,

    /// Metadata
    pub metadata: MemoryMetadata,

    /// Access control
    pub access_control: AccessControl,

    /// When the entry was created
    pub created_at: DateTime<Utc>,

    /// When the entry was last updated
    pub updated_at: DateTime<Utc>,

    /// Version for optimistic locking
    pub version: u32,
}

impl MemoryEntry {
    /// Create a new memory entry
    pub fn new(user_id: Uuid, content: impl Into<String>) -> Self {
        let now = Utc::now();
        Self {
            id: ulid::Ulid::new().to_string(),
            user_id,
            content: content.into(),
            embedding: None,
            metadata: MemoryMetadata::default(),
            access_control: AccessControl::default(),
            created_at: now,
            updated_at: now,
            version: 1,
        }
    }

    /// Create a memory entry from a conversation
    pub fn from_conversation(user_id: Uuid, content: impl Into<String>) -> Self {
        let mut entry = Self::new(user_id, content);
        entry.metadata.source = MemorySource::Conversation;
        entry
    }

    /// Set the embedding vector
    pub fn with_embedding(mut self, embedding: Vec<f32>) -> Self {
        self.embedding = Some(embedding);
        self
    }

    /// Add tags to the memory
    pub fn with_tags(mut self, tags: Vec<String>) -> Self {
        self.metadata.tags = tags;
        self
    }

    /// Set the importance score
    pub fn with_importance(mut self, score: f32) -> Self {
        self.metadata.importance_score = score.clamp(0.0, 1.0);
        self
    }

    /// Record an access to this memory
    pub fn record_access(&mut self) {
        self.metadata.access_frequency += 1;
        self.metadata.last_accessed = Utc::now();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_memory_entry_creation() {
        let entry = MemoryEntry::new(Uuid::new_v4(), "Test memory");
        assert_eq!(entry.content, "Test memory");
        assert_eq!(entry.version, 1);
    }

    #[test]
    fn test_memory_with_embedding() {
        let embedding = vec![0.1, 0.2, 0.3];
        let entry = MemoryEntry::new(Uuid::new_v4(), "Test")
            .with_embedding(embedding.clone());

        assert_eq!(entry.embedding, Some(embedding));
    }

    #[test]
    fn test_record_access() {
        let mut entry = MemoryEntry::new(Uuid::new_v4(), "Test");
        assert_eq!(entry.metadata.access_frequency, 0);

        entry.record_access();
        assert_eq!(entry.metadata.access_frequency, 1);

        entry.record_access();
        assert_eq!(entry.metadata.access_frequency, 2);
    }
}
