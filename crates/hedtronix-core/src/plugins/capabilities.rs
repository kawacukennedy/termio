//! Plugin capabilities and permissions
//!
//! Capability-based security model for plugins.

use serde::{Deserialize, Serialize};
use std::collections::HashSet;

/// Granular permission for a specific resource
#[derive(Debug, Clone, Hash, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Permission {
    /// Network access
    Network { hosts: Vec<String> },
    /// Filesystem access
    Filesystem { paths: Vec<String>, read_only: bool },
    /// AI model access
    AiCompute,
    /// Memory/Knowledge base access
    MemoryRead,
    MemoryWrite,
    /// Audio input access
    AudioRecord,
    /// Notification access
    Notifications,
}

/// Collection of capabilities granted to a plugin
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Capabilities {
    pub permissions: HashSet<Permission>,
}

impl Capabilities {
    /// Create new empty capabilities
    pub fn new() -> Self {
        Self {
            permissions: HashSet::new(),
        }
    }

    /// Check if a specific permission is granted
    pub fn has_permission(&self, permission: &Permission) -> bool {
        // Simple exact match for now
        // In check_network or check_fs we'd logic for host/path matching
        self.permissions.contains(permission)
    }

    /// Check network access for a host
    pub fn check_network(&self, host: &str) -> bool {
        for perm in &self.permissions {
            if let Permission::Network { hosts } = perm {
                if hosts.contains(&"*".to_string()) || hosts.contains(&host.to_string()) {
                    return true;
                }
            }
        }
        false
    }

    /// Check filesystem access
    pub fn check_fs(&self, path: &str, write: bool) -> bool {
        for perm in &self.permissions {
            if let Permission::Filesystem { paths, read_only } = perm {
                if write && *read_only {
                    continue;
                }
                // Check if path starts with allowed path
                for allowed in paths {
                    if path.starts_with(allowed) {
                        return true;
                    }
                }
            }
        }
        false
    }
}
