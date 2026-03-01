//! Device identity keys
//!
//! Ed25519 key pairs for device identification and signing.
//!
//! # Overview
//!
//! Each TERMIO device generates a unique Ed25519 key pair on first run.
//! This key pair is used for:
//!
//! - **Device Identification**: Public key serves as device identity
//! - **Message Signing**: Sign sync messages for verification
//! - **Plugin Signatures**: Verify plugin integrity
//!
//! # Security
//!
//! - Private keys NEVER leave the device
//! - Keys are stored encrypted at rest (via the encryption module)
//! - Public keys can be shared for verification
//!
//! # Usage
//!
//! ```rust
//! use termio_core::auth::DeviceKey;
//!
//! // Generate new key pair
//! let key = DeviceKey::generate();
//!
//! // Get public key for sharing
//! let public_key = key.public_key();
//!
//! // Sign data
//! let signature = key.sign(b"Hello TERMIO");
//!
//! // Verify signature
//! use ed25519_dalek::Verifier;
//! public_key.verify(b"Hello TERMIO", &signature.into()).unwrap();
//! ```

use ed25519_dalek::{Signer, SigningKey, VerifyingKey};
use rand::rngs::OsRng;
use serde::{Deserialize, Serialize};
use std::fmt;

use crate::error::{Error, Result};

/// A device key pair for signing and identity
///
/// Ed25519 provides fast signing with high security.
/// The key pair consists of:
///
/// - **Signing Key32 ( bytes)**: Kept secret, used for signing
/// - **Verifying Key (32 bytes)**: Can be shared, used for verification
pub struct DeviceKey {
    /// The Ed25519 signing key
    signing_key: SigningKey,
}

impl DeviceKey {
    /// Generate a new random device key
    ///
    /// Uses the operating system's cryptographically secure random
    /// number generator (CSRNG) via `OsRng`.
    ///
    /// # Returns
    ///
    /// A new DeviceKey with randomly generated private key
    ///
    /// # Example
    ///
    /// ```rust
    /// let key = DeviceKey::generate();
    /// let public = key.public_key();
    /// println!("New device: {:?}", public);
    /// ```
    pub fn generate() -> Self {
        // Generate 32 random bytes for the seed
        let mut secret_bytes = [0u8; 32];
        rand::RngCore::fill_bytes(&mut OsRng, &mut secret_bytes);
        let signing_key = SigningKey::from_bytes(&secret_bytes);
        Self { signing_key }
    }

    /// Create from existing bytes
    ///
    /// Use to restore a key from stored seed.
    /// MUST be exactly 32 bytes.
    ///
    /// # Arguments
    ///
    /// * `bytes` - 32-byte private key seed
    ///
    /// # Panics
    ///
    /// Panics if bytes is not exactly 32 bytes
    pub fn from_bytes(bytes: &[u8; 32]) -> Self {
        let signing_key = SigningKey::from_bytes(bytes);
        Self { signing_key }
    }

    /// Get the public verifying key
    ///
    /// The public key can be safely shared.
    /// Used for device identification and signature verification.
    ///
    /// # Returns
    ///
    /// The 32-byte Ed25519 public key
    pub fn public_key(&self) -> VerifyingKey {
        self.signing_key.verifying_key()
    }

    /// Sign data
    ///
    /// Creates an Ed25519 signature over the provided data.
    ///
    /// # Arguments
    ///
    /// * `data` - Data to sign
    ///
    /// # Returns
    ///
    /// 64-byte Ed25519 signature
    pub fn sign(&self, data: &[u8]) -> [u8; 64] {
        self.signing_key.sign(data).to_bytes()
    }

    /// Get the raw private key bytes
    ///
    /// WARNING: These bytes can be used to sign as this device.
    /// Store securely, never transmit unencrypted.
    ///
    /// # Returns
    ///
    /// 32-byte private key
    pub fn to_bytes(&self) -> [u8; 32] {
        self.signing_key.to_bytes()
    }
}

/// Serializable key pair
///
/// Format for storing/serializing device keys.
/// Both keys are Base64 encoded for safe string storage.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyPair {
    /// Base64 encoded public key
    pub public_key: String,
    /// Base64 encoded private key (WARNING: sensitive!)
    pub private_key: String,
}

impl DeviceKey {
    /// Export as serializable key pair
    ///
    /// Converts the key pair to a storable format.
    /// The private key is NOT encrypted - encryption should be
    /// applied separately if storing persistently.
    ///
    /// # Returns
    ///
    /// KeyPair with Base64-encoded keys
    pub fn to_key_pair(&self) -> KeyPair {
        use base64::{engine::general_purpose::STANDARD, Engine};
        
        let public = self.public_key();
        let private = self.signing_key.to_bytes();

        KeyPair {
            public_key: STANDARD.encode(public.as_bytes()),
            private_key: STANDARD.encode(private),
        }
    }

    /// Import from serializable key pair
    ///
    /// Restores a DeviceKey from stored KeyPair.
    ///
    /// # Arguments
    ///
    /// * `pair` - Previously exported KeyPair
    ///
    /// # Returns
    ///
    /// Restored DeviceKey
    pub fn from_key_pair(pair: &KeyPair) -> Result<Self> {
        use base64::{engine::general_purpose::STANDARD, Engine};

        // Decode the private key
        let private_bytes = STANDARD
            .decode(&pair.private_key)
            .map_err(|e| Error::Auth(format!("Invalid private key encoding: {}", e)))?;

        // Validate length
        if private_bytes.len() != 32 {
            return Err(Error::Auth("Invalid private key length".to_string()));
        }

        // Copy to fixed-size array
        let mut bytes = [0u8; 32];
        bytes.copy_from_slice(&private_bytes);

        Ok(Self::from_bytes(&bytes))
    }
}

impl fmt::Debug for DeviceKey {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "DeviceKey(public: {:?})", self.public_key())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sign_verify() {
        let key = DeviceKey::generate();
        let data = b"Verify this data";
        
        let signature = key.sign(data);
        let public_key = key.public_key();
        
        use ed25519_dalek::Verifier;
        let sig = ed25519_dalek::Signature::from_bytes(&signature);
        assert!(public_key.verify(data, &sig).is_ok());
    }

    #[test]
    fn test_serialization() {
        let key = DeviceKey::generate();
        let pair = key.to_key_pair();
        
        let restored = DeviceKey::from_key_pair(&pair).unwrap();
        assert_eq!(key.public_key(), restored.public_key());
    }
}
