//! TERMIO Core Library
//!
//! This crate provides shared functionality for all TERMIO components:
//! - Data models for conversations, messages, and memory entries
//! - Three-tier memory architecture (ring buffer, vector store, persistent)
//! - Voice recognition with Vosk STT
//! - Cryptography and authentication
//! - Event system for pub/sub communication
//! - Plugin system with WASM runtime
//! - Cross-device synchronization
//! - Notification system
//! - Health monitoring
//! - Configuration management
//! - Error types and handling
//!
//! # Architecture
//!
//! The core is organized into several key modules:
//!
//! - [`auth`] - Device identity and JWT session management
//! - [`config`] - Hierarchical configuration loading
//! - [`crypto`] - AES-256-GCM encryption and Argon2id key derivation
//! - [`error`] - Centralized error handling with error codes
//! - [`events`] - Async pub/sub event bus for component communication
//! - [`health`] - System health checking and reporting
//! - [`memory`] - Three-tier memory (ring buffer, vector, persistent)
//! - [`models`] - All data structures (Conversation, Message, etc.)
//! - [`notifications`] - User notification system with priorities
//! - [`payments`] - Payment processor webhooks
//! - [`plugins`] - WASM plugin runtime with capabilities
//! - [`sync`] - P2P sync using CRDTs and libp2p
//! - [`voice`] - Audio recording and speech recognition

/// Authentication module - device keys and JWT sessions
pub mod auth;
/// Configuration management - loads from TOML files and environment
pub mod config;
/// Cryptography - AES-256-GCM encryption and Argon2id key derivation
pub mod crypto;
/// Central error types with codes for categorization
pub mod error;
/// Event system - async pub/sub for inter-component communication
pub mod events;
/// Health monitoring - system resource and service availability checks
pub mod health;
/// Three-tier memory system - ring buffer, vector store, SQLite persistent
pub mod memory;
/// All data models - Conversation, Message, MemoryEntry, etc.
pub mod models;
/// Notification system - priorities, quiet hours, filtering
pub mod notifications;
/// Payment processing - Stripe and Binance webhooks
pub mod payments;
/// Plugin ecosystem - WASM runtime with capability security
pub mod plugins;
/// Cross-device sync - CRDTs, delta sync, peer management
pub mod sync;
/// Voice input - audio recording and Vosk speech recognition
pub mod voice;

/// Re-export Config for convenience - main application configuration
pub use config::Config;
/// Re-export Error and Result for convenience - central error handling
pub use error::{Error, Result};
