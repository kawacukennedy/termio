//! Conversation model
//!
//! A conversation represents a multi-message chat session between a user
//! and the AI assistant. Conversations are the primary unit of interaction
//! in TERMIO.
//!
//! # Structure
//!
//! Each conversation contains:
//! - Unique identifier (UUID v7 for time-ordering)
//! - User and device identifiers (for multi-device sync)
//! - Session ID for grouping related conversations
//! - Vector of messages
//! - Context window information (token count, embeddings status)
//! - Timestamps for creation and last update
//! - Vector clock for CRDT sync
//!
//! # Lifecycle
//!
//! 1. **Created**: New conversation with empty messages
//! 2. **Active**: User and assistant messages added
//! 3. **Archived**: Marked inactive by user
//! 4. **Deleted**: Soft-deleted, retained for sync conflict resolution
//!
//! # Example
//!
//! ```rust
//! use termio_core::models::{Conversation, Message};
//! use uuid::Uuid;
//!
//! let mut conv = Conversation::new(user_id, device_id);
//! conv.add_message(Message::user("Hello"));
//! conv.add_message(Message::assistant("Hi there!"));
//! ```

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::Message;

/// Context window information for a conversation
///
/// Tracks token usage and embeddings status for the conversation.
/// Used for:
///
/// - Enforcing token limits
/// - Deciding when to compress/summarize
/// - Tracking if semantic embeddings have been generated
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextWindow {
    /// Current token count in the context
    /// Updated after each message add
    pub token_count: usize,

    /// Whether embeddings have been generated
    /// Vector embeddings enable semantic search
    pub embeddings_generated: bool,

    /// Summary of the conversation (for context compression)
    /// Generated when conversation exceeds token limits
    /// Allows retaining conversation essence with fewer tokens
    pub summary: Option<String>,
}

impl Default for ContextWindow {
    fn default() -> Self {
        Self {
            token_count: 0,
            embeddings_generated: false,
            summary: None,
        }
    }
}

/// A conversation containing multiple messages
///
/// This is the main data structure for chat sessions. Each conversation
/// belongs to a user and device, and can be synced across devices.
///
/// # Storage
///
/// Conversations are stored in SQLite with the following schema:
/// - id: UUID v7 (primary key)
/// - user_id: UUID v4
/// - device_id: UUID v4
/// - session_id: UUID v4 (for grouping)
/// - messages: JSON array
/// - context_window: JSON object
/// - created_at: RFC3339
/// - updated_at: RFC3339
/// - vector_timestamp: JSON array (CRDT)
/// - status: string (active/archived/deleted)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Conversation {
    /// Unique conversation ID (UUID v7 for time-ordering)
    /// UUID v7 embeds timestamp, enabling sort by ID
    pub id: Uuid,

    /// User who owns this conversation
    /// Used for multi-user isolation
    pub user_id: Uuid,

    /// Device where conversation was created
    /// Used for device attribution and sync
    pub device_id: Uuid,

    /// Session ID for grouping related conversations
    /// All conversations in a session share context
    pub session_id: Uuid,

    /// Messages in the conversation
    /// Ordered chronologically, oldest first
    pub messages: Vec<Message>,

    /// Context window information
    /// Tracks token usage and embeddings status
    pub context_window: ContextWindow,

    /// When the conversation was created
    /// Set at construction time, never modified
    pub created_at: DateTime<Utc>,

    /// When the conversation was last updated
    /// Updated after each message add
    pub updated_at: DateTime<Utc>,

    /// Vector timestamp for CRDT sync
    /// Used for conflict resolution in distributed systems
    pub vector_timestamp: Vec<i64>,

    /// Conversation status (active, archived, deleted)
    /// Soft-delete allows sync conflict recovery
    #[serde(default = "default_status")]
    pub status: String,
}

/// Default status for new conversations
fn default_status() -> String {
    "active".to_string()
}

impl Conversation {
    /// Create a new conversation
    ///
    /// Initializes with empty messages and default context window.
    /// Sets timestamps to current UTC time.
    ///
    /// # Arguments
    ///
    /// * `user_id` - The user who owns this conversation
    /// * `device_id` - The device where conversation was created
    ///
    /// # Returns
    ///
    /// A new Conversation with generated IDs and timestamps
    ///
    /// # Example
    ///
    /// ```rust
    /// use termio_core::models::Conversation;
    /// use uuid::Uuid;
    ///
    /// let conv = Conversation::new(user_id, device_id);
    /// assert!(conv.is_empty());
    /// ```
    pub fn new(user_id: Uuid, device_id: Uuid) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::now_v7(),           // UUID v7 for time-ordered ID
            user_id,
            device_id,
            session_id: Uuid::new_v4(),   // New session for new conversation
            messages: Vec::new(),
            context_window: ContextWindow::default(),
            created_at: now,
            updated_at: now,
            vector_timestamp: Vec::new(),
            status: "active".to_string(),
        }
    }

    /// Add a message to the conversation
    ///
    /// Appends a message and updates the last-modified timestamp.
    /// Does NOT update token count - caller must do that separately.
    ///
    /// # Arguments
    ///
    /// * `message` - The message to add (user or assistant)
    ///
    /// # Example
    ///
    /// ```rust
    /// use termio_core::models::{Conversation, Message};
    ///
    /// let mut conv = Conversation::default();
    /// conv.add_message(Message::user("Hello"));
    /// assert_eq!(conv.len(), 1);
    /// ```
    pub fn add_message(&mut self, message: Message) {
        self.messages.push(message);
        self.updated_at = Utc::now();
    }

    /// Get the last N messages
    ///
    /// Returns the most recent messages, useful for context window
    /// when recent messages are most relevant.
    ///
    /// # Arguments
    ///
    /// * `n` - Number of messages to return
    ///
    /// # Returns
    ///
    /// Slice of the last N messages, or all if fewer than N
    pub fn last_messages(&self, n: usize) -> &[Message] {
        let start = self.messages.len().saturating_sub(n);
        &self.messages[start..]
    }

    /// Check if the conversation is empty
    ///
    /// # Returns
    ///
    /// True if no messages have been added
    pub fn is_empty(&self) -> bool {
        self.messages.is_empty()
    }

    /// Get the message count
    ///
    /// # Returns
    ///
    /// Number of messages in the conversation
    pub fn len(&self) -> usize {
        self.messages.len()
    }

    /// Update the token count
    ///
    /// Called after adding messages to track context usage.
    /// Used for enforcing token limits.
    ///
    /// # Arguments
    ///
    /// * `count` - Current token count for context
    pub fn set_token_count(&mut self, count: usize) {
        self.context_window.token_count = count;
    }
}

impl Default for Conversation {
    /// Creates a default conversation with random user/device IDs
    ///
    /// Useful for testing and prototyping.
    fn default() -> Self {
        Self::new(Uuid::new_v4(), Uuid::new_v4())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_conversation_creation() {
        let conv = Conversation::default();
        assert!(conv.is_empty());
        assert_eq!(conv.len(), 0);
    }

    #[test]
    fn test_add_message() {
        let mut conv = Conversation::default();
        conv.add_message(Message::user("Hello"));
        conv.add_message(Message::assistant("Hi there!"));

        assert_eq!(conv.len(), 2);
        assert!(!conv.is_empty());
    }

    #[test]
    fn test_last_messages() {
        let mut conv = Conversation::default();
        for i in 0..10 {
            conv.add_message(Message::user(format!("Message {}", i)));
        }

        let last_3 = conv.last_messages(3);
        assert_eq!(last_3.len(), 3);
        assert_eq!(last_3[0].content, "Message 7");
    }
}
