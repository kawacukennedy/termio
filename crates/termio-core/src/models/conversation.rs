//! Conversation model

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::Message;

/// Context window information for a conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextWindow {
    /// Current token count in the context
    pub token_count: usize,

    /// Whether embeddings have been generated
    pub embeddings_generated: bool,

    /// Summary of the conversation (for context compression)
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
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Conversation {
    /// Unique conversation ID (UUID v7)
    pub id: Uuid,

    /// User who owns this conversation
    pub user_id: Uuid,

    /// Device where conversation was created
    pub device_id: Uuid,

    /// Session ID for grouping related conversations
    pub session_id: Uuid,

    /// Messages in the conversation
    pub messages: Vec<Message>,

    /// Context window information
    pub context_window: ContextWindow,

    /// When the conversation was created
    pub created_at: DateTime<Utc>,

    /// When the conversation was last updated
    pub updated_at: DateTime<Utc>,

    /// Vector timestamp for CRDT sync
    pub vector_timestamp: Vec<i64>,

    /// Conversation status (active, archived, deleted)
    #[serde(default = "default_status")]
    pub status: String,
}

fn default_status() -> String {
    "active".to_string()
}

impl Conversation {
    /// Create a new conversation
    pub fn new(user_id: Uuid, device_id: Uuid) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::now_v7(),
            user_id,
            device_id,
            session_id: Uuid::new_v4(),
            messages: Vec::new(),
            context_window: ContextWindow::default(),
            created_at: now,
            updated_at: now,
            vector_timestamp: Vec::new(),
            status: "active".to_string(),
        }
    }

    /// Add a message to the conversation
    pub fn add_message(&mut self, message: Message) {
        self.messages.push(message);
        self.updated_at = Utc::now();
    }

    /// Get the last N messages
    pub fn last_messages(&self, n: usize) -> &[Message] {
        let start = self.messages.len().saturating_sub(n);
        &self.messages[start..]
    }

    /// Check if the conversation is empty
    pub fn is_empty(&self) -> bool {
        self.messages.is_empty()
    }

    /// Get the message count
    pub fn len(&self) -> usize {
        self.messages.len()
    }

    /// Update the token count
    pub fn set_token_count(&mut self, count: usize) {
        self.context_window.token_count = count;
    }
}

impl Default for Conversation {
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
