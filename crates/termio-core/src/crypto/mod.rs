//! Cryptography module
//!
//! This module provides cryptographic primitives for TERMIO:
//!
//! - **Encryption**: AES-256-GCM authenticated encryption for data at rest
//! - **Key Derivation**: Argon2id for secure password-based key derivation
//!
//! # Security Model
//!
//! All encryption uses AES-256-GCM which provides:
//! - **Confidentiality**: Data cannot be read without the key
//! - **Integrity**: Tampering with encrypted data is detected
//! - **Authentication**: Proven that data came from key holder
//!
//! # Usage
//!
//! ```rust
//! use termio_core::crypto::{encrypt, decrypt};
//!
//! // Generate or load key (32 bytes for AES-256)
//! let key = [0u8; 32];
//!
//! // Encrypt
//! let encrypted = encrypt(&key, b"secret message")?;
//!
//! // Decrypt
//! let decrypted = decrypt(&key, &encrypted)?;
//! assert_eq!(decrypted, b"secret message");
//! ```

mod encryption;
mod key_derivation;

pub use encryption::{decrypt, encrypt, EncryptedData};
pub use key_derivation::{derive_key, DerivedKey};
