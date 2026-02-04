//! Ring buffer for recent context
//!
//! Fast in-memory storage for the last N items.
//! Provides O(1) insertion and O(1) access to recent items.

use std::collections::VecDeque;

/// A fixed-size ring buffer for storing recent items
#[derive(Debug, Clone)]
pub struct RingBuffer<T> {
    buffer: VecDeque<T>,
    capacity: usize,
}

impl<T> RingBuffer<T> {
    /// Create a new ring buffer with the given capacity
    pub fn new(capacity: usize) -> Self {
        Self {
            buffer: VecDeque::with_capacity(capacity),
            capacity,
        }
    }

    /// Push an item to the buffer, removing the oldest if at capacity
    pub fn push(&mut self, item: T) {
        if self.buffer.len() >= self.capacity {
            self.buffer.pop_front();
        }
        self.buffer.push_back(item);
    }

    /// Get the most recent item
    pub fn last(&self) -> Option<&T> {
        self.buffer.back()
    }

    /// Get the oldest item
    pub fn first(&self) -> Option<&T> {
        self.buffer.front()
    }

    /// Get the last N items (most recent first)
    pub fn last_n(&self, n: usize) -> Vec<&T> {
        self.buffer.iter().rev().take(n).collect()
    }

    /// Get all items in chronological order
    pub fn iter(&self) -> impl Iterator<Item = &T> {
        self.buffer.iter()
    }

    /// Get the number of items in the buffer
    pub fn len(&self) -> usize {
        self.buffer.len()
    }

    /// Check if the buffer is empty
    pub fn is_empty(&self) -> bool {
        self.buffer.is_empty()
    }

    /// Check if the buffer is full
    pub fn is_full(&self) -> bool {
        self.buffer.len() >= self.capacity
    }

    /// Get the capacity of the buffer
    pub fn capacity(&self) -> usize {
        self.capacity
    }

    /// Clear all items from the buffer
    pub fn clear(&mut self) {
        self.buffer.clear();
    }
}

impl<T> Default for RingBuffer<T> {
    fn default() -> Self {
        Self::new(100) // Default from spec: 100 interactions
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_push_and_get() {
        let mut buffer = RingBuffer::new(3);
        buffer.push(1);
        buffer.push(2);
        buffer.push(3);

        assert_eq!(buffer.len(), 3);
        assert_eq!(buffer.last(), Some(&3));
        assert_eq!(buffer.first(), Some(&1));
    }

    #[test]
    fn test_overflow() {
        let mut buffer = RingBuffer::new(3);
        buffer.push(1);
        buffer.push(2);
        buffer.push(3);
        buffer.push(4); // Should remove 1

        assert_eq!(buffer.len(), 3);
        assert_eq!(buffer.first(), Some(&2));
        assert_eq!(buffer.last(), Some(&4));
    }

    #[test]
    fn test_last_n() {
        let mut buffer = RingBuffer::new(5);
        for i in 1..=5 {
            buffer.push(i);
        }

        let last_3: Vec<_> = buffer.last_n(3);
        assert_eq!(last_3, vec![&5, &4, &3]);
    }

    #[test]
    fn test_is_full() {
        let mut buffer = RingBuffer::new(2);
        assert!(!buffer.is_full());

        buffer.push(1);
        assert!(!buffer.is_full());

        buffer.push(2);
        assert!(buffer.is_full());
    }
}
