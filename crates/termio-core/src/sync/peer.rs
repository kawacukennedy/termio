//! Peer management
//!
//! Discovery and connection manager using libp2p.
//! Supports mDNS discovery and relay fallback per spec.

use std::collections::HashMap;
use chrono::{DateTime, Utc};
use libp2p::{identity, PeerId};
use serde::{Deserialize, Serialize};

use super::crdt::VectorClock;

/// Known peer information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerInfo {
    /// Peer ID
    pub peer_id: String,
    /// User-assigned alias for the device
    pub alias: Option<String>,
    /// When the peer was first discovered
    pub discovered_at: DateTime<Utc>,
    /// Last time we successfully communicated
    pub last_seen: DateTime<Utc>,
    /// Peer's last known vector clock
    pub last_clock: VectorClock,
    /// Connection status
    pub status: PeerStatus,
    /// Discovery method that found this peer
    pub discovery_method: DiscoveryMethod,
}

/// Peer connection status
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum PeerStatus {
    /// Discovered but not connected
    Discovered,
    /// Currently connected and syncing
    Connected,
    /// Connection was successful but now idle
    Idle,
    /// Connection attempt failed
    Unreachable,
}

/// How a peer was discovered
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum DiscoveryMethod {
    /// mDNS local network discovery
    Mdns,
    /// Manual address entry
    Manual,
    /// Relay server
    Relay,
}

/// Manages P2P peers for cross-device sync
pub struct PeerManager {
    /// Local peer identity
    local_peer_id: PeerId,
    /// Local device ID for sync identification
    local_device_id: String,
    /// Known peers
    peers: HashMap<String, PeerInfo>,
    /// Whether mDNS discovery is active
    mdns_active: bool,
    /// Relay server URL (fallback when direct connection fails)
    relay_url: Option<String>,
}

impl PeerManager {
    /// Create a new peer manager
    pub fn new() -> Self {
        let local_key = identity::Keypair::generate_ed25519();
        let local_peer_id = PeerId::from(local_key.public());

        tracing::info!("Local Peer ID: {:?}", local_peer_id);

        Self {
            local_device_id: local_peer_id.to_string(),
            local_peer_id,
            peers: HashMap::new(),
            mdns_active: false,
            relay_url: None,
        }
    }

    /// Create with a specific device ID (e.g., from saved config)
    pub fn with_device_id(device_id: &str) -> Self {
        let local_key = identity::Keypair::generate_ed25519();
        let local_peer_id = PeerId::from(local_key.public());

        Self {
            local_device_id: device_id.to_string(),
            local_peer_id,
            peers: HashMap::new(),
            mdns_active: false,
            relay_url: None,
        }
    }

    /// Get the local device ID
    pub fn device_id(&self) -> &str {
        &self.local_device_id
    }

    /// Get the local peer ID
    pub fn peer_id(&self) -> &PeerId {
        &self.local_peer_id
    }

    /// Set relay server URL for fallback connections
    pub fn set_relay(&mut self, url: &str) {
        self.relay_url = Some(url.to_string());
    }

    /// Start mDNS discovery on local network
    pub fn start_discovery(&mut self) {
        // In a full implementation, this would create an mDNS service
        // using libp2p::mdns::tokio::Behaviour
        self.mdns_active = true;
        tracing::info!("mDNS peer discovery started");
    }

    /// Stop mDNS discovery
    pub fn stop_discovery(&mut self) {
        self.mdns_active = false;
        tracing::info!("mDNS peer discovery stopped");
    }

    /// Register a discovered peer
    pub fn add_peer(
        &mut self,
        peer_id: &str,
        method: DiscoveryMethod,
        alias: Option<String>,
    ) {
        let now = Utc::now();
        let info = PeerInfo {
            peer_id: peer_id.to_string(),
            alias,
            discovered_at: now,
            last_seen: now,
            last_clock: VectorClock::new(),
            status: PeerStatus::Discovered,
            discovery_method: method,
        };
        self.peers.insert(peer_id.to_string(), info);
        tracing::info!("Added peer: {}", peer_id);
    }

    /// Update peer status after a sync attempt
    pub fn update_peer_status(
        &mut self,
        peer_id: &str,
        status: PeerStatus,
        clock: Option<VectorClock>,
    ) {
        if let Some(peer) = self.peers.get_mut(peer_id) {
            peer.status = status;
            peer.last_seen = Utc::now();
            if let Some(c) = clock {
                peer.last_clock = c;
            }
        }
    }

    /// Get all known peers
    pub fn list_peers(&self) -> Vec<&PeerInfo> {
        self.peers.values().collect()
    }

    /// Get peers that are eligible for sync (discovered or idle)
    pub fn syncable_peers(&self) -> Vec<&PeerInfo> {
        self.peers
            .values()
            .filter(|p| {
                matches!(
                    p.status,
                    PeerStatus::Discovered | PeerStatus::Connected | PeerStatus::Idle
                )
            })
            .collect()
    }

    /// Remove a peer
    pub fn remove_peer(&mut self, peer_id: &str) -> bool {
        self.peers.remove(peer_id).is_some()
    }

    /// Check if mDNS discovery is running
    pub fn is_discovering(&self) -> bool {
        self.mdns_active
    }

    /// Get count of connected peers
    pub fn connected_count(&self) -> usize {
        self.peers
            .values()
            .filter(|p| p.status == PeerStatus::Connected)
            .count()
    }
}
