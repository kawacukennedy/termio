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

        vc1.merge(&vc2); // vc1 has {A:1, B:1}
        assert_eq!(vc2.partial_cmp(&vc1), Some(Ordering::Less)); // vc2 < vc1

        vc1.increment("A"); // vc1 has {A:2, B:1}
        assert_eq!(vc2.partial_cmp(&vc1), Some(Ordering::Less));
    }
}
