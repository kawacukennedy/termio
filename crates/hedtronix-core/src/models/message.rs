//! Message model

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Role of the message sender
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Role {
    /// User message
    User,
    /// AI assistant response
    Assistant,
    /// System prompt or instruction
    System,
}

/// Input mode for the message
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum InputMode {
    /// Typed text input
    Text,
    /// Voice input (STT)
    Voice,
    /// Screen interaction
    Screen,
}

/// Metadata for a message
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageMetadata {
    /// How the message was input
    pub input_mode: InputMode,

    /// Confidence score (0-1) for voice/screen input
    pub confidence: Option<f32>,

    /// Which model was used for AI responses
    pub model_used: Option<String>,

    /// Processing time in milliseconds
    pub processing_time_ms: Option<u64>,
}

impl Default for MessageMetadata {
    fn default() -> Self {
        Self {
            input_mode: InputMode::Text,
            confidence: None,
            model_used: None,
            processing_time_ms: None,
        }
    }
}

/// A single message in a conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    /// Unique message ID (UUID v7 for time-ordering)
    pub id: Uuid,

    /// Message role
    pub role: Role,

    /// Message content
    pub content: String,

    /// When the message was created
    pub timestamp: DateTime<Utc>,

    /// Additional metadata
    pub metadata: MessageMetadata,
}

impl Message {
    /// Create a new user message
    pub fn user(content: impl Into<String>) -> Self {
        Self {
            id: Uuid::now_v7(),
            role: Role::User,
            content: content.into(),
            timestamp: Utc::now(),
            metadata: MessageMetadata::default(),
        }
    }

    /// Create a new assistant message
    pub fn assistant(content: impl Into<String>) -> Self {
        Self {
            id: Uuid::now_v7(),
            role: Role::Assistant,
            content: content.into(),
            timestamp: Utc::now(),
            metadata: MessageMetadata::default(),
        }
    }

    /// Create a new system message
    pub fn system(content: impl Into<String>) -> Self {
        Self {
            id: Uuid::now_v7(),
            role: Role::System,
            content: content.into(),
            timestamp: Utc::now(),
            metadata: MessageMetadata::default(),
        }
    }

    /// Set the model used for this message
    pub fn with_model(mut self, model: impl Into<String>) -> Self {
        self.metadata.model_used = Some(model.into());
        self
    }

    /// Set the processing time
    pub fn with_processing_time(mut self, ms: u64) -> Self {
        self.metadata.processing_time_ms = Some(ms);
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_message_creation() {
        let msg = Message::user("Hello, world!");
        assert_eq!(msg.role, Role::User);
        assert_eq!(msg.content, "Hello, world!");
    }

    #[test]
    fn test_message_with_metadata() {
        let msg = Message::assistant("Hi there!")
            .with_model("llama-7b")
            .with_processing_time(150);

        assert_eq!(msg.metadata.model_used, Some("llama-7b".to_string()));
        assert_eq!(msg.metadata.processing_time_ms, Some(150));
    }
}
