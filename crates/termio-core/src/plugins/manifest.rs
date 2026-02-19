//! Plugin manifest
//!
//! Metadata and configuration for plugins.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::capabilities::Permission;

/// Plugin entry points
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntryPoints {
    pub wasm_module: String,
    pub initialize: String,
    pub cleanup: String,
}

/// Plugin signature for verification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginSignature {
    pub algorithm: String,
    pub value: String,
    pub timestamp: DateTime<Utc>,
}

/// Version compatibility range
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Compatibility {
    pub min_core_version: String,
    pub max_core_version: Option<String>,
    pub platforms: Vec<String>,
}

/// Plugin manifest definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginManifest {
    pub id: Uuid,
    pub name: String,
    pub version: String,
    pub description: Option<String>,
    pub author: Author,
    pub permissions: Vec<Permission>,
    pub entry_points: EntryPoints,
    pub signature: Option<PluginSignature>,
    pub compatibility: Compatibility,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Author {
    pub name: String,
    pub email: Option<String>,
    pub url: Option<String>,
    pub public_key: Option<String>,
}

impl PluginManifest {
    /// Verify manifest integrity
    pub fn validate(&self) -> crate::error::Result<()> {
        if self.name.is_empty() {
            return Err(crate::error::Error::Configuration("Plugin name cannot be empty".to_string()));
        }
        if self.entry_points.wasm_module.is_empty() {
            return Err(crate::error::Error::Configuration("WASM module path cannot be empty".to_string()));
        }
        Ok(())
    }

    /// Check if this plugin is compatible with a given core version
    pub fn is_compatible(&self, core_version: &str) -> bool {
        // Simple semver comparison — in production use the semver crate
        core_version >= self.compatibility.min_core_version.as_str()
            && self.compatibility.max_core_version
                .as_ref()
                .map_or(true, |max| core_version <= max.as_str())
    }

    /// Verify signature (stub — real impl would use ed25519)
    pub fn verify_signature(&self) -> bool {
        self.signature.is_some()
    }
}
