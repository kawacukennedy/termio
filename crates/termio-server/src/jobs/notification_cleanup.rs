//! Notification cleanup background job
//!
//! Checks expired notifications and retries failed deliveries.
//! Spec: runs every 15 minutes.

use crate::state::AppState;

/// Run notification cleanup
pub async fn run(state: &AppState) {
    tracing::debug!("Running notification cleanup...");

    // Step 1: Remove expired notifications
    let expired = remove_expired(state).await;
    if expired > 0 {
        tracing::info!("Removed {} expired notifications", expired);
    }

    // Step 2: Deliver scheduled notifications that are ready
    let delivered = deliver_ready(state).await;
    if delivered > 0 {
        tracing::info!("Delivered {} scheduled notifications", delivered);
    }

    // Step 3: Persist current notification state to database
    persist_notifications(state).await;

    tracing::debug!("Notification cleanup completed");
}

/// Remove expired notifications
async fn remove_expired(state: &AppState) -> usize {
    state.notification_manager.check_expirations()
}

/// Deliver notifications whose scheduled time has arrived
async fn deliver_ready(state: &AppState) -> usize {
    let delivered = state.notification_manager.deliver_ready();
    delivered.len()
}

/// Persist notifications to database
async fn persist_notifications(state: &AppState) {
    if let Err(e) = state.notification_manager.persist_to_db() {
        tracing::error!("Failed to persist notifications: {}", e);
    }
}
