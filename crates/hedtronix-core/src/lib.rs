//! HEDTRONIX Core Library
//!
//! This crate provides shared functionality for all HEDTRONIX components:
//! - Data models for conversations, messages, and memory entries
//! - Three-tier memory architecture (ring buffer, vector store, persistent)
//! - Voice recognition with Vosk STT
//! - Cryptography and authentication
//! - Event system for pub/sub communication
//! - Plugin system with WASM runtime
//! - Cross-device synchronization
//! - Configuration management
//! - Error types and handling

pub mod auth;
pub mod config;
pub mod crypto;
pub mod error;
pub mod events;
pub mod memory;
pub mod models;
pub mod plugins;
pub mod sync;
pub mod voice;

pub use config::Config;
pub use error::{Error, Result};

