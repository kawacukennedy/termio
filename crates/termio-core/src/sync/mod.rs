//! Cross-device synchronization
//!
//! P2P sync using CRDTs and libp2p.
//! Supports mDNS discovery with relay fallback.

mod crdt;
mod delta;
mod peer;

pub use crdt::{ConflictResolution, CrdtRegister, VectorClock};
pub use delta::{Delta, DeltaStore, Operation, SyncConflict};
pub use peer::{DiscoveryMethod, PeerInfo, PeerManager, PeerStatus};
