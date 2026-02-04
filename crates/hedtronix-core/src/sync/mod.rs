//! Cross-device synchronization
//!
//! P2P sync using CRDTs and libp2p.

mod crdt;
mod delta;
mod peer;

pub use crdt::VectorClock;
pub use peer::PeerManager;
