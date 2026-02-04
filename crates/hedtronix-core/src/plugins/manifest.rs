//! Plugin manifest
//!
//! Metadata and configuration for plugins.

use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::capabilities::Permission;

/// Plugin manifest definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginManifest {
    pub id: Uuid,
    pub name: String,
    pub version: String,
    pub description: Option<String>,
    pub author: Author,
    pub permissions: Vec<Permission>,
    pub entry_point: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Author {
    pub name: String,
    pub email: Option<String>,
    pub url: Option<String>,
}

impl PluginManifest {
    /// Verify manifest integrity
    pub fn validate(&self) -> crate::error::Result<()> {
        if self.name.is_empty() {
            return Err(crate::error::Error::Configuration("Plugin name cannot be empty".to_string()));
        }
        // TODO: Validate version string format (semver)
        Ok(())
    }
}
