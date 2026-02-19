//! Data models for TERMIO
//!
//! Implements the data models from the specification:
//! - Conversation: Multi-message conversation with context
//! - Message: Individual message with metadata
//! - MemoryEntry: Semantic memory with embeddings
//! - KnowledgeNode/Edge: Graph-based knowledge representation
//! - Document: Uploaded document processing
//! - HealthData: Biometric and health measurements
//! - ActionPlan: Autonomous task execution plans
//! - DeviceSyncState: Cross-device sync tracking

mod action_plan;
mod conversation;
mod device_sync;
mod document;
mod health_data;
mod knowledge_graph;
mod memory_entry;
mod message;

pub use action_plan::{ActionPlan, ActionStep, ActionType, PlanStatus};
pub use conversation::Conversation;
pub use device_sync::{DeviceSyncState, SyncConfig, LastSync, PendingChanges, ConnectionInfo};
pub use document::{Document, DocumentStatus, DocumentType};
pub use health_data::{HealthData, HealthDataSource, HealthDataType, HealthDataMetadata};
pub use knowledge_graph::{KnowledgeEdge, KnowledgeNode};
pub use memory_entry::{MemoryEntry, MemorySource, SharingPolicy};
pub use message::{InputMode, Message, MessageMetadata, Role};

