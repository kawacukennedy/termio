//! Delta synchronization
//!
//! Efficient state sync using deltas with conflict resolution.

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

use crate::models::{Conversation, Message};
use super::crdt::{VectorClock, ConflictResolution};

/// A state change delta
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Delta {
    pub id: Uuid,
    pub source_node: String,
    pub version: VectorClock,
    pub operation: Operation,
    pub timestamp: DateTime<Utc>,
}

impl Delta {
    /// Create a new delta
    pub fn new(source_node: &str, version: VectorClock, operation: Operation) -> Self {
        Self {
            id: Uuid::new_v4(),
            source_node: source_node.to_string(),
            version,
            operation,
            timestamp: Utc::now(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Operation {
    UpsertConversation(Conversation),
    DeleteConversation(Uuid),
    AddMessage(Message),
    /// Generic key-value update for extensibility
    SetValue {
        collection: String,
        key: String,
        value: serde_json::Value,
    },
    /// Delete a record by collection and key
    DeleteRecord {
        collection: String,
        key: String,
    },
}

/// Conflict that occurred during sync
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncConflict {
    pub id: Uuid,
    pub local_delta: Delta,
    pub remote_delta: Delta,
    pub resolved: bool,
    pub resolution: Option<ConflictResolution>,
    pub winner: Option<String>, // "local" or "remote"
}

/// Delta store for tracking change history
pub struct DeltaStore {
    /// In-memory buffer of recent deltas
    deltas: Vec<Delta>,
    /// Maximum deltas to retain
    max_size: usize,
    /// Unresolved conflicts
    conflicts: Vec<SyncConflict>,
}

impl DeltaStore {
    pub fn new() -> Self {
        Self {
            deltas: Vec::new(),
            max_size: 10_000,
            conflicts: Vec::new(),
        }
    }

    /// Create with custom capacity
    pub fn with_capacity(max_size: usize) -> Self {
        Self {
            deltas: Vec::with_capacity(max_size.min(1000)),
            max_size,
            conflicts: Vec::new(),
        }
    }

    /// Add a new delta
    pub fn add(&mut self, delta: Delta) {
        self.deltas.push(delta);
        // Evict oldest if over capacity
        if self.deltas.len() > self.max_size {
            self.deltas.remove(0);
        }
    }

    /// Get deltas that happened after the given vector clock
    pub fn get_since(&self, version: &VectorClock) -> Vec<Delta> {
        self.deltas
            .iter()
            .filter(|d| d.version.dominates(version) || d.version.is_concurrent(version))
            .cloned()
            .collect()
    }

    /// Compute delta between local and remote state
    pub fn compute_delta(
        &self,
        local_clock: &VectorClock,
        remote_clock: &VectorClock,
    ) -> Vec<Delta> {
        self.deltas
            .iter()
            .filter(|d| {
                // Include deltas that remote hasn't seen
                d.version.dominates(remote_clock) || d.version.is_concurrent(remote_clock)
            })
            .filter(|d| {
                // But only those that local has
                !d.version.dominates(local_clock)
                    || d.version == *local_clock
                    || local_clock.dominates(&d.version)
            })
            .cloned()
            .collect()
    }

    /// Apply remote deltas, detecting conflicts
    pub fn apply_remote_deltas(
        &mut self,
        remote_deltas: Vec<Delta>,
        _local_clock: &VectorClock,
        resolution: &ConflictResolution,
    ) -> Vec<SyncConflict> {
        let mut new_conflicts = Vec::new();

        for remote_delta in remote_deltas {
            // Check for concurrent local modifications
            let concurrent_local: Vec<_> = self
                .deltas
                .iter()
                .filter(|local| local.version.is_concurrent(&remote_delta.version))
                .filter(|local| self.operations_conflict(&local.operation, &remote_delta.operation))
                .cloned()
                .collect();

            if concurrent_local.is_empty() {
                // No conflict — apply directly
                self.add(remote_delta);
            } else {
                // Conflict detected
                for local_delta in concurrent_local {
                    let winner = match resolution {
                        ConflictResolution::LastWriterWins => {
                            if remote_delta.timestamp > local_delta.timestamp {
                                "remote"
                            } else {
                                "local"
                            }
                        }
                        ConflictResolution::KeepBoth => "both",
                        ConflictResolution::Custom(_) => "manual",
                    };

                    let conflict = SyncConflict {
                        id: Uuid::new_v4(),
                        local_delta: local_delta.clone(),
                        remote_delta: remote_delta.clone(),
                        resolved: winner != "manual",
                        resolution: Some(resolution.clone()),
                        winner: Some(winner.to_string()),
                    };
                    new_conflicts.push(conflict);
                }

                // For LWW, still apply the winner
                match resolution {
                    ConflictResolution::LastWriterWins | ConflictResolution::KeepBoth => {
                        self.add(remote_delta);
                    }
                    ConflictResolution::Custom(_) => {
                        // Wait for manual resolution
                    }
                }
            }
        }

        self.conflicts.extend(new_conflicts.clone());
        new_conflicts
    }

    /// Check if two operations conflict (modify the same resource)
    fn operations_conflict(&self, a: &Operation, b: &Operation) -> bool {
        match (a, b) {
            (Operation::UpsertConversation(c1), Operation::UpsertConversation(c2)) => {
                c1.id == c2.id
            }
            (Operation::DeleteConversation(id1), Operation::UpsertConversation(c2)) => {
                *id1 == c2.id
            }
            (Operation::UpsertConversation(c1), Operation::DeleteConversation(id2)) => {
                c1.id == *id2
            }
            (
                Operation::SetValue { collection: c1, key: k1, .. },
                Operation::SetValue { collection: c2, key: k2, .. },
            ) => c1 == c2 && k1 == k2,
            (
                Operation::SetValue { collection: c1, key: k1, .. },
                Operation::DeleteRecord { collection: c2, key: k2 },
            ) => c1 == c2 && k1 == k2,
            (
                Operation::DeleteRecord { collection: c1, key: k1 },
                Operation::SetValue { collection: c2, key: k2, .. },
            ) => c1 == c2 && k1 == k2,
            _ => false,
        }
    }

    /// Get unresolved conflicts
    pub fn unresolved_conflicts(&self) -> Vec<&SyncConflict> {
        self.conflicts.iter().filter(|c| !c.resolved).collect()
    }

    /// Total delta count
    pub fn len(&self) -> usize {
        self.deltas.len()
    }

    /// Whether the store is empty
    pub fn is_empty(&self) -> bool {
        self.deltas.is_empty()
    }
}
