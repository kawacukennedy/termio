//! Ring buffer for recent context
//!
//! Fast in-memory storage for the last N items.
//! Provides O(1) insertion and O(1) access to recent items.
//!
//! # How It Works
//!
//! The ring buffer maintains a fixed-size queue. When full, adding
//! a new item automatically removes the oldest item. This implements
//! "least recently used" (LRU) eviction automatically.
//!
//! # Performance
//!
//! - Push: O(1) amortized
//! - Access: O(1)
//! - Memory: Fixed capacity (no reallocation)
//!
//! # Usage
//!
//! ```rust
//! use termio_core::memory::RingBuffer;
//!
//! let mut buffer = RingBuffer::new(3);  // Max 3 items
//! buffer.push(1);
//! buffer.push(2);
//! buffer.push(3);
//! buffer.push(4);  // 1 is evicted
//!
//! assert_eq!(buffer.first(), Some(&2));  // Oldest remaining
//! assert_eq!(buffer.last(), Some(&4));   // Most recent
//! ```

use std::collections::VecDeque;

/// A fixed-size ring buffer for storing recent items
///
/// Implements circular buffer with automatic eviction of oldest items.
#[derive(Debug, Clone)]
pub struct RingBuffer<T> {
    /// Internal storage using VecDeque for O(1) at both ends
    buffer: VecDeque<T>,
    /// Maximum number of items to store
    capacity: usize,
}

impl<T> RingBuffer<T> {
    /// Create a new ring buffer with the given capacity
    ///
    /// # Arguments
    ///
    /// * `capacity` - Maximum number of items to store
    ///
    /// # Example
    ///
    /// ```rust
    /// let buffer = RingBuffer::<String>::new(100);
    /// assert!(buffer.is_empty());
    /// ```
    pub fn new(capacity: usize) -> Self {
        Self {
            buffer: VecDeque::with_capacity(capacity),
            capacity,
        }
    }

    /// Push an item to the buffer, removing the oldest if at capacity
    ///
    /// If buffer is full, removes the oldest item first.
    ///
    /// # Arguments
    ///
    /// * `item` - Item to add
    pub fn push(&mut self, item: T) {
        // If full, remove oldest item first
        if self.buffer.len() >= self.capacity {
            self.buffer.pop_front();
        }
        self.buffer.push_back(item);
    }

    /// Get the most recent item
    ///
    /// # Returns
    ///
    /// Reference to the last item, or None if empty
    pub fn last(&self) -> Option<&T> {
        self.buffer.back()
    }

    /// Get the oldest item
    ///
    /// # Returns
    ///
    /// Reference to the first item, or None if empty
    pub fn first(&self) -> Option<&T> {
        self.buffer.front()
    }

    /// Get the last N items (most recent first)
    ///
    /// Returns items in reverse chronological order.
    ///
    /// # Arguments
    ///
    /// * `n` - Number of items to return
    ///
    /// # Returns
    ///
    /// Vector of references to the most recent N items
    pub fn last_n(&self, n: usize) -> Vec<&T> {
        self.buffer.iter().rev().take(n).collect()
    }

    /// Get all items in chronological order
    ///
    /// # Returns
    ///
    /// Iterator over all items, oldest first
    pub fn iter(&self) -> impl Iterator<Item = &T> {
        self.buffer.iter()
    }

    /// Get an item by index
    ///
    /// Index 0 is the oldest item.
    ///
    /// # Arguments
    ///
    /// * `index` - Position in buffer (0 = oldest)
    ///
    /// # Returns
    ///
    /// Reference to item at index, or None if out of bounds
    pub fn get(&self, index: usize) -> Option<&T> {
        self.buffer.get(index)
    }

    /// Get the number of items in the buffer
    ///
    /// # Returns
    ///
    /// Current item count (0 to capacity)
    pub fn len(&self) -> usize {
        self.buffer.len()
    }

    /// Check if the buffer is empty
    ///
    /// # Returns
    ///
    /// true if no items stored
    pub fn is_empty(&self) -> bool {
        self.buffer.is_empty()
    }

    /// Check if the buffer is full
    ///
    /// # Returns
    ///
    /// true if at capacity
    pub fn is_full(&self) -> bool {
        self.buffer.len() >= self.capacity
    }

    /// Get the capacity of the buffer
    ///
    /// # Returns
    ///
    /// Maximum number of items that can be stored
    pub fn capacity(&self) -> usize {
        self.capacity
    }

    /// Clear all items from the buffer
    ///
    /// Removes all items. Capacity remains unchanged.
    pub fn clear(&mut self) {
        self.buffer.clear();
    }
}

impl<T> Default for RingBuffer<T> {
    /// Default capacity of 100 (per spec)
    fn default() -> Self {
        Self::new(100)
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
