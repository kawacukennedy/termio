//! Sync polling background job
//!
//! Checks for pending sync changes and attempts P2P reconciliation.
//! Spec: runs every 5 minutes.

use crate::state::AppState;

/// Run sync polling
pub async fn run(state: &AppState) {
    tracing::debug!("Running sync poll...");

    // Step 1: Check for pending local changes
    let pending_count = check_pending_changes(state).await;
    if pending_count == 0 {
        tracing::debug!("No pending sync changes");
        return;
    }

    tracing::info!("Found {} pending sync changes", pending_count);

    // Step 2: Discover available peers
    let peers = discover_peers(state).await;
    if peers.is_empty() {
        tracing::debug!("No peers available for sync");
        return;
    }

    // Step 3: Attempt sync with each peer
    for peer_id in &peers {
        match sync_with_peer(state, peer_id).await {
            Ok(synced) => {
                tracing::info!("Synced {} changes with peer {}", synced, peer_id);
            }
            Err(e) => {
                tracing::warn!("Failed to sync with peer {}: {}", peer_id, e);
            }
        }
    }

    tracing::info!("Sync polling completed");
}

/// Check for pending local changes that need to be synced
async fn check_pending_changes(state: &AppState) -> usize {
    let store = state.memory_store.read().await;
    // Count entries modified since last known sync point
    store.count_unindexed_entries().await.unwrap_or(0) as usize
}

/// Discover available peers via the event bus
async fn discover_peers(state: &AppState) -> Vec<String> {
    // Query the event bus for recently seen sync peers
    // In production this would use mDNS or a signalling server
    let _bus = &state.event_bus;

    // For now, check if any SyncEvent::Connected events were published recently
    // This will be populated once libp2p networking is wired in PeerManager
    Vec::new()
}

/// Attempt to sync with a specific peer
async fn sync_with_peer(
    _state: &AppState,
    peer_id: &str,
) -> Result<usize, String> {
    // In a full implementation:
    // 1. Connect to peer via libp2p transport
    // 2. Exchange vector clocks to determine divergence
    // 3. Compute deltas using DeltaStore::compute_delta()
    // 4. Send/receive deltas
    // 5. Apply remote deltas with conflict resolution
    // 6. Publish SyncCompleted event
    tracing::debug!("Would sync with peer {} (P2P not yet wired)", peer_id);
    Ok(0)
}
