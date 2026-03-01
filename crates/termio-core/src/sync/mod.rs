//! Cross-device synchronization
//!
//! P2P sync using CRDTs and libp2p.
//! Supports mDNS discovery with relay fallback.
//!
//! # Architecture
//!
//! ## CRDT (Conflict-free Replicated Data Types)
//!
//! Enables automatic conflict resolution in distributed systems:
//! - Vector Clocks: Track causality between changes
//! - LWW Register: Last-Writer-Wins for simple values
//! - Delta Store: Efficient change tracking
//!
//! ## Peer-to-Peer Sync
//!
//! - **Discovery**: mDNS for local network, manual for remote
//! - **Transport**: libp2p for encrypted P2P connections
//! - **Fallback**: Relay servers when direct connection unavailable
//!
//! ## Conflict Resolution
//!
//! 1. **Vector Clocks**: Track which device made each change
//! 2. **Automatic Merge**: Most conflicts resolved automatically
//! 3. **Conflict Tombstone**: Unresolvable conflicts marked for manual review
//!
//! # Usage
//!
//! ```rust
//! use termio_core::sync::{PeerManager, DeltaStore, CrdtRegister};
//!
//! // Peer management
//! let mut peer_manager = PeerManager::new();
//! peer_manager.start_discovery();
//!
//! // CRDT Register for automatic sync
//! let mut register = CrdtRegister::new("value".to_string(), "device_a");
//! register.set("new_value");
//! ```

mod crdt;
mod delta;
mod peer;

pub use crdt::{ConflictResolution, CrdtRegister, VectorClock};
pub use delta::{Delta, DeltaStore, Operation, SyncConflict};
pub use peer::{DiscoveryMethod, PeerInfo, PeerManager, PeerStatus};
