//! Three-tier memory architecture
//!
//! Implements the memory system from the specification:
//! 1. Ring buffer: Last 100 interactions in memory
//! 2. Vector store: Semantic search across history
//! 3. Persistent storage: Encrypted SQLite database

mod ring_buffer;
mod store;
mod vector_store;

pub use ring_buffer::RingBuffer;
pub use store::MemoryStore;
pub use vector_store::{VectorEntry, VectorStore};

