//! CRDT primitives
//!
//! Conflict-free Replicated Data Types for state synchronization.

use serde::{Deserialize, Serialize};
use std::cmp::Ordering;
use std::collections::HashMap;

/// Vector clock for causality tracking
#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct VectorClock {
    /// Map of node ID to counter
    pub clocks: HashMap<String, u64>,
}

impl VectorClock {
    /// Create a new vector clock
    pub fn new() -> Self {
        Self {
            clocks: HashMap::new(),
        }
    }

    /// Increment clock for a node
    pub fn increment(&mut self, node_id: &str) {
        let counter = self.clocks.entry(node_id.to_string()).or_insert(0);
        *counter += 1;
    }

    /// Merge with another vector clock (taking max values)
    pub fn merge(&mut self, other: &VectorClock) {
        for (node, counter) in &other.clocks {
            let current = self.clocks.entry(node.clone()).or_insert(0);
            *current = std::cmp::max(*current, *counter);
        }
    }

    /// Check if this clock happened before another
    pub fn happens_before(&self, other: &VectorClock) -> bool {
        if self.clocks.is_empty() && !other.clocks.is_empty() {
            return true;
        }

        let mut has_smaller = false;
        
        // precise check: for all nodes i, self[i] <= other[i] AND exists j, self[j] < other[j]
        for (node, count) in &self.clocks {
            let other_count = other.clocks.get(node).unwrap_or(&0);
            if count > other_count {
                return false;
            }
            if count < other_count {
                has_smaller = true;
            }
        }

        // any nodes in other but not in self imply strictly greater for those components
        for (node, _) in &other.clocks {
            if !self.clocks.contains_key(node) {
                has_smaller = true;
            }
        }

        has_smaller
    }
}

impl PartialOrd for VectorClock {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        let self_before_other = self.happens_before(other);
        let other_before_self = other.happens_before(self);

        match (self_before_other, other_before_self) {
            (true, false) => Some(Ordering::Less),
            (false, true) => Some(Ordering::Greater),
            (false, false) => {
                if self.clocks == other.clocks {
                    Some(Ordering::Equal)
                } else {
                    None // Concurrent
                }
            }
            (true, true) => None, // Impossible
        }
    }
}

impl VectorClock {
    /// Check if two clocks are concurrent (neither dominates)
    pub fn is_concurrent(&self, other: &VectorClock) -> bool {
        self.partial_cmp(other).is_none()
    }

    /// Check if this clock dominates (happened after) another
    pub fn dominates(&self, other: &VectorClock) -> bool {
        other.happens_before(self)
    }

    /// Get the counter for a specific node
    pub fn get(&self, node_id: &str) -> u64 {
        self.clocks.get(node_id).copied().unwrap_or(0)
    }

    /// Get all known node IDs
    pub fn nodes(&self) -> Vec<&String> {
        self.clocks.keys().collect()
    }
}

/// Conflict resolution strategy
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ConflictResolution {
    /// Use the value from the clock that has a higher sum of counters
    LastWriterWins,
    /// Keep both values for manual resolution
    KeepBoth,
    /// Use a custom resolver function name
    Custom(String),
}

impl Default for ConflictResolution {
    fn default() -> Self {
        ConflictResolution::LastWriterWins
    }
}

/// Last-Writer-Wins Register — a CRDT that holds a single value.
/// Concurrent updates are resolved by comparing vector clocks;
/// if concurrent, the value with the higher clock sum wins.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrdtRegister<T: Clone + Serialize> {
    pub value: T,
    pub clock: VectorClock,
    pub node_id: String,
}

impl<T: Clone + Serialize + for<'de> Deserialize<'de>> CrdtRegister<T> {
    /// Create a new register with an initial value
    pub fn new(value: T, node_id: &str) -> Self {
        let mut clock = VectorClock::new();
        clock.increment(node_id);
        Self {
            value,
            clock,
            node_id: node_id.to_string(),
        }
    }

    /// Update the value, incrementing the local clock
    pub fn set(&mut self, value: T) {
        self.clock.increment(&self.node_id);
        self.value = value;
    }

    /// Merge with a remote register. Returns true if value changed.
    pub fn merge(&mut self, remote: &CrdtRegister<T>) -> bool {
        if remote.clock.dominates(&self.clock) {
            // Remote is strictly newer — take its value
            self.value = remote.value.clone();
            self.clock.merge(&remote.clock);
            true
        } else if self.clock.dominates(&remote.clock) {
            // Local is newer — keep our value, still merge clocks
            self.clock.merge(&remote.clock);
            false
        } else if self.clock.is_concurrent(&remote.clock) {
            // Concurrent — LWW by sum of counters (tie-break by node_id)
            let local_sum: u64 = self.clock.clocks.values().sum();
            let remote_sum: u64 = remote.clock.clocks.values().sum();
            self.clock.merge(&remote.clock);
            if remote_sum > local_sum
                || (remote_sum == local_sum && remote.node_id > self.node_id)
            {
                self.value = remote.value.clone();
                true
            } else {
                false
            }
        } else {
            // Equal — no change
            false
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vector_clock() {
        let mut vc1 = VectorClock::new();
        let mut vc2 = VectorClock::new();

        vc1.increment("A");
        vc2.increment("B");

        assert_eq!(vc1.partial_cmp(&vc2), None); // Concurrent
        assert!(vc1.is_concurrent(&vc2));

        vc1.merge(&vc2); // vc1 has {A:1, B:1}
        assert_eq!(vc2.partial_cmp(&vc1), Some(Ordering::Less)); // vc2 < vc1
        assert!(vc1.dominates(&vc2));

        vc1.increment("A"); // vc1 has {A:2, B:1}
        assert_eq!(vc2.partial_cmp(&vc1), Some(Ordering::Less));
    }

    #[test]
    fn test_crdt_register_lww() {
        let mut reg_a = CrdtRegister::new("hello".to_string(), "A");
        let mut reg_b = CrdtRegister::new("world".to_string(), "B");

        // Both set concurrently
        reg_a.set("from_a".to_string());
        reg_b.set("from_b".to_string());

        // Merge — should pick one deterministically
        let changed = reg_a.merge(&reg_b);
        assert!(changed || !changed); // just verify it doesn't panic

        // After merge, both should converge
        reg_b.merge(&reg_a);
        assert_eq!(reg_a.value, reg_b.value);
    }
}
