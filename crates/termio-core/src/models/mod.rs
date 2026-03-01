//! Data models for TERMIO
//!
//! This module contains all data structures used throughout TERMIO,
//! implementing the data models from the project specification.
//!
//! # Model Overview
//!
//! | Model | Description | Storage |
//! |-------|-------------|---------|
//! | Conversation | Multi-message chat with context | SQLite |
//! | Message | Individual user/assistant message | In Conversation |
//! | MemoryEntry | Semantic memory with embeddings | SQLite + Vector |
//! | KnowledgeNode | Graph entity | SQLite |
//! | KnowledgeEdge | Graph relationship | SQLite |
//! | Document | Uploaded document | SQLite |
//! | HealthData | Biometric measurements | SQLite |
//! | ActionPlan | Autonomous task plan | SQLite |
//! | DeviceSyncState | Cross-device sync state | SQLite |
//! | Subscription | User subscription tier | SQLite |
//! | SmartDevice | Matter/Thread device | SQLite |
//!
//! # Key Design Decisions
//!
//! - UUID v7 for time-ordered IDs (conversation, message, memory)
//! - ULID for memory entries (time-ordered, sortable)
//! - RFC3339 timestamps for all temporal fields
//! - Serde for JSON serialization throughout

mod action_plan;
mod conversation;
mod device_sync;
mod document;
mod health_data;
mod knowledge_graph;
mod memory_entry;
mod message;
pub mod smart_home;
pub mod subscription;

pub use action_plan::{ActionPlan, ActionStep, ActionType, PlanStatus};
pub use conversation::Conversation;
pub use device_sync::{DeviceSyncState, SyncConfig, LastSync, PendingChanges, ConnectionInfo};
pub use document::{Document, DocumentStatus, DocumentType};
pub use health_data::{HealthData, HealthDataSource, HealthDataType, HealthDataMetadata};
pub use knowledge_graph::{KnowledgeEdge, KnowledgeNode};
pub use memory_entry::{MemoryEntry, MemorySource, SharingPolicy};
pub use message::{InputMode, Message, MessageMetadata, Role};

