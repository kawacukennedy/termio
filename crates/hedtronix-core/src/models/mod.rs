//! Data models for HEDTRONIX
//!
//! Implements the data models from the specification:
//! - Conversation: Multi-message conversation with context
//! - Message: Individual message with metadata
//! - MemoryEntry: Semantic memory with embeddings

mod conversation;
mod memory_entry;
mod message;

pub use conversation::Conversation;
pub use memory_entry::{MemoryEntry, MemorySource, SharingPolicy};
pub use message::{InputMode, Message, MessageMetadata, Role};
