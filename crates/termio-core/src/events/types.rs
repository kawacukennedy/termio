//! Event definitions
//!
//! Structured events for the system event bus.
//!
//! ## Event Categories
//!
//! | Category | Description | Use Case |
//! |----------|-------------|----------|
//! | System | Lifecycle events | Logging, monitoring |
//! | Conversation | Chat events | UI updates, sync |
//! | AI | Model events | Progress, debugging |
//! | Memory | Storage events | Indexing, cleanup |
//! | Sync | P2P events | Connection status |
//!
//! ## Event Structure
//!
//! ```rust
//! Event {
//!     id: "ulid...",
//!     timestamp: "2024-01-15T10:30:00Z",
//!     payload: EventPayload::Conversation(ConversationEvent::MessageReceived(msg)),
//!     source: "termio-core"
//! }
//! ```

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::models::{Message, Conversation};

/// A system event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    /// Unique event ID
    pub id: Uuid,
    /// When the event occurred
    pub timestamp: DateTime<Utc>,
    /// The event payload
    pub payload: EventPayload,
    /// Component that emitted the event
    pub source: String,
}

impl Event {
    /// Create a new event
    pub fn new(payload: EventPayload, source: impl Into<String>) -> Self {
        Self {
            id: Uuid::new_v4(),
            timestamp: Utc::now(),
            payload,
            source: source.into(),
        }
    }
}

/// Event payload types
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", content = "data")]
pub enum EventPayload {
    /// System lifecycle events
    System(SystemEvent),
    /// Conversation events
    Conversation(ConversationEvent),
    /// AI Processing events
    Ai(AiEvent),
    /// Memory/Storage events
    Memory(MemoryEvent),
    /// Device Sync events
    Sync(SyncEvent),
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SystemEvent {
    Startup,
    Shutdown,
    Error { code: u16, message: String },
    ConfigReload,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ConversationEvent {
    Created(Conversation),
    MessageReceived(Message),
    MessageSent(Message),
    Updated(Uuid),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AiEvent {
    RequestStarted { request_id: Uuid },
    TokenGenerated { request_id: Uuid, token: String },
    ResponseCompleted { request_id: Uuid, tokens: usize, time_ms: u64 },
    Error { request_id: Uuid, error: String },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MemoryEvent {
    EntryCreated { id: String },
    EntryUpdated { id: String },
    SearchPerformed { query: String, results: usize },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SyncEvent {
    Connected { peer_id: String },
    Disconnected { peer_id: String },
    SyncStarted,
    SyncCompleted { changes: usize },
    ConflictDetected { id: String },
}
