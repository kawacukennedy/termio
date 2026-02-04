//! Delta synchronization
//!
//! Efficient state sync using deltas.

use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::models::{Conversation, Message};
use super::crdt::VectorClock;

/// A state change delta
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Delta {
    pub id: Uuid,
    pub source_node: String,
    pub version: VectorClock,
    pub operation: Operation,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Operation {
    UpsertConversation(Conversation),
    DeleteConversation(Uuid),
    AddMessage(Message),
}

/// Delta store for tracking history
pub struct DeltaStore {
    // In-memory buffer of recent deltas
    deltas: Vec<Delta>,
}

impl DeltaStore {
    pub fn new() -> Self {
        Self { deltas: Vec::new() }
    }

    pub fn add(&mut self, delta: Delta) {
        self.deltas.push(delta);
    }

    pub fn get_since(&self, _version: &VectorClock) -> Vec<Delta> {
        // Simple implementation: return all deltas
        // Real implementation would filter based on vector clock
        self.deltas.clone()
    }
}
