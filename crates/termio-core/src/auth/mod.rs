//! Authentication module
//!
//! This module provides device identity and session management for TERMIO.
//! It handles:
//!
//! - **Device Keys**: Ed25519 key pairs for device identification
//! - **Session Management**: JWT-based authentication tokens
//!
//! # Security Model
//!
//! 1. Each device generates a unique Ed25519 key pair on first run
//! 2. Sessions are authenticated via JWT tokens signed with the device key
//! 3. Tokens contain user ID, device ID, permissions, and expiration
//! 4. Token verification ensures requests come from authenticated devices
//!
//! # Error Handling
//!
//! All authentication errors use the `Error::Auth` variant with descriptive messages.

mod device_key;
mod session;

pub use device_key::{DeviceKey, KeyPair};
pub use session::{Session, SessionManager, Token};
