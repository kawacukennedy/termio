//! Device sync state model
//!
//! Tracks synchronization state for each paired device (FA-010).
//!
//! ## Overview
//!
//! TERMIO uses CRDTs (Conflict-free Replicated Data Types) for eventual
//! consistency across devices. This model tracks:
//! - Last sync timestamp and state hash
//! - Pending changes waiting to sync
//! - Connection info for peer-to-peer sync
//! - User preferences for sync behavior
//!
//! ## Sync Configuration
//!
//! | Setting | Default | Description |
//! |---------|---------|-------------|
//! | auto_sync | true | Automatically sync when changes occur |
//! | wifi_only | false | Only sync on WiFi (save mobile data) |
//! | battery_threshold | 20% | Minimum battery to trigger sync |
//! | data_cap_mb | None | Monthly data limit (None = unlimited) |
//!
//! ## Vector Clocks
//!
//! Each sync maintains a vector clock to track causality:
//! - `{ "device_A": 5, "device_B": 3 }` means device_A has 5 events, device_B has 3
//! - Used to resolve conflicts in CRDT merge operations

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LastSync {
    pub timestamp: DateTime<Utc>,
    pub vector_clock: HashMap<String, u64>,
    pub hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PendingChanges {
    pub count: u64,
    pub size_bytes: u64,
    pub oldest: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectionInfo {
    pub last_ip: Option<String>,
    pub last_connection: Option<DateTime<Utc>>,
    pub protocol_version: u32,
    pub supported_features: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncConfig {
    pub auto_sync: bool,
    pub wifi_only: bool,
    pub battery_threshold: u8,
    pub data_cap_mb: Option<u64>,
}

impl Default for SyncConfig {
    fn default() -> Self {
        Self {
            auto_sync: true,
            wifi_only: false,
            battery_threshold: 20,
            data_cap_mb: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeviceSyncState {
    pub device_id: Uuid,
    pub user_id: Uuid,
    pub last_sync: LastSync,
    pub pending_changes: PendingChanges,
    pub connection_info: ConnectionInfo,
    pub sync_config: SyncConfig,
}

impl DeviceSyncState {
    pub fn new(device_id: Uuid, user_id: Uuid) -> Self {
        Self {
            device_id,
            user_id,
            last_sync: LastSync {
                timestamp: Utc::now(),
                vector_clock: HashMap::new(),
                hash: String::new(),
            },
            pending_changes: PendingChanges {
                count: 0,
                size_bytes: 0,
                oldest: None,
            },
            connection_info: ConnectionInfo {
                last_ip: None,
                last_connection: None,
                protocol_version: 1,
                supported_features: vec!["crdt".into(), "delta_sync".into()],
            },
            sync_config: SyncConfig::default(),
        }
    }

    pub fn should_sync(&self, battery_level: u8, on_wifi: bool) -> bool {
        if !self.sync_config.auto_sync { return false; }
        if battery_level < self.sync_config.battery_threshold { return false; }
        if self.sync_config.wifi_only && !on_wifi { return false; }
        true
    }

    pub fn record_sync(&mut self, hash: String, vector_clock: HashMap<String, u64>) {
        self.last_sync = LastSync { timestamp: Utc::now(), vector_clock, hash };
        self.pending_changes = PendingChanges { count: 0, size_bytes: 0, oldest: None };
    }

    pub fn add_pending_change(&mut self, size_bytes: u64) {
        self.pending_changes.count += 1;
        self.pending_changes.size_bytes += size_bytes;
        if self.pending_changes.oldest.is_none() {
            self.pending_changes.oldest = Some(Utc::now());
        }
    }
}
