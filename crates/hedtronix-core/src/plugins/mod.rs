//! Plugin ecosystem
//!
//! WASM-based plugin system with capability security.

mod capabilities;
mod manifest;
mod runtime;

pub use capabilities::{Capabilities, Permission};
pub use manifest::PluginManifest;
pub use runtime::PluginRuntime;
