//! Plugin ecosystem
//!
//! WASM-based plugin system with capability security.
//!
//! # Overview
//!
//! TERMIO supports extensible plugins written in any language that compiles
//! to WebAssembly. Plugins run in a sandboxed environment with strict
//! capability controls.
//!
//! # Security Model
//!
//! ## Capability-Based Access
//!
//! Plugins declare required capabilities in their manifest:
//! - Network: External API access
//! - Filesystem: Read/write to specific paths
//! - AI Compute: Access to AI models
//! - Memory: Read/write to memory store
//! - Audio: Microphone access
//! - Notifications: Send notifications
//!
//! ## Sandboxing
//!
//! - **Runtime**: Wasmtime with limited resources
//! - **Memory**: 64MB max per plugin
//! - **CPU**: 100ms max per invocation
//! - **Network**: Blocked unless capability granted
//! - **Filesystem**: Restricted to declared paths
//!
//! # Plugin Structure
//!
//! Each plugin requires:
//! - Manifest (plugin.json): Name, version, capabilities, entry points
//! - WASM module: Compiled plugin code
//! - Signature: Ed25519 signature for integrity
//!
//! # Example Manifest
//!
//! ```json
//! {
//!   "name": "weather-plugin",
//!   "version": "1.0.0",
//!   "capabilities": ["network", "notifications"],
//!   "entry_points": {
//!     "wasm_module": "plugin.wasm",
//!     "initialize": "init",
//!     "cleanup": "cleanup"
//!   }
//! }
//! ```

mod capabilities;
mod manifest;
mod runtime;

pub use capabilities::{Capabilities, Permission};
pub use manifest::PluginManifest;
pub use runtime::PluginRuntime;
