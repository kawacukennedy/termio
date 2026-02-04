//! Cryptography module
//!
//! AES-256-GCM encryption and Argon2id key derivation.

mod encryption;
mod key_derivation;

pub use encryption::{decrypt, encrypt, EncryptedData};
pub use key_derivation::{derive_key, DerivedKey};
