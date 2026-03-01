//! Three-tier memory architecture
//!
//! TERMIO implements a three-tier memory system as specified:
//!
//! # Tier 1: Ring Buffer
//! - **Storage**: In-memory `VecDeque`
//! - **Capacity**: Last 100 interactions (per spec)
//! - **Latency**: <1ms (O(1) access)
//! - **Purpose**: Recent context for immediate AI responses
//!
//! # Tier 2: Vector Store
//! - **Storage**: SQLite with BLOBs for embeddings
//! - **Search**: Cosine similarity semantic search
//! - **Dimensions**: 768 (per spec)
//! - **Purpose**: Find relevant past context
//!
//! # Tier 3: Persistent Storage
//! - **Storage**: SQLite database
//! - **Encryption**: AES-256-GCM at rest
//! - **Purpose**: Long-term memory, knowledge graph
//!
//! # Usage
//!
//! ```rust
//! use termio_core::memory::{RingBuffer, MemoryStore, VectorStore};
//!
//! // Ring buffer for recent context
//! let mut buffer = RingBuffer::new(100);
//! buffer.push(message);
//!
//! // Persistent storage
//! let store = MemoryStore::new("termio.db").await?;
//! store.save_conversation(&conv).await?;
//! ```

mod ring_buffer;
mod store;
mod vector_store;

pub use ring_buffer::RingBuffer;
pub use store::MemoryStore;
pub use vector_store::{VectorEntry, VectorStore};

