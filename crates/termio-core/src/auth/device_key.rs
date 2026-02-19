//! Device identity keys
//!
//! Ed25519 key pairs for device identification and signing.

use ed25519_dalek::{Signer, SigningKey, VerifyingKey};
use rand::rngs::OsRng;
use serde::{Deserialize, Serialize};
use std::fmt;

use crate::error::{Error, Result};

/// A device key pair for signing and identity
pub struct DeviceKey {
    signing_key: SigningKey,
}

impl DeviceKey {
    /// Generate a new random device key
    pub fn generate() -> Self {
        let mut secret_bytes = [0u8; 32];
        rand::RngCore::fill_bytes(&mut OsRng, &mut secret_bytes);
        let signing_key = SigningKey::from_bytes(&secret_bytes);
        Self { signing_key }
    }

    /// Create from bytes
    pub fn from_bytes(bytes: &[u8; 32]) -> Self {
        let signing_key = SigningKey::from_bytes(bytes);
        Self { signing_key }
    }

    /// Get the public verifying key
    pub fn public_key(&self) -> VerifyingKey {
        self.signing_key.verifying_key()
    }

    /// Sign data
    pub fn sign(&self, data: &[u8]) -> [u8; 64] {
        self.signing_key.sign(data).to_bytes()
    }

    /// Get the raw private key bytes
    pub fn to_bytes(&self) -> [u8; 32] {
        self.signing_key.to_bytes()
    }
}

/// Serializable key pair
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyPair {
    pub public_key: String,  // Base64 encoded
    pub private_key: String, // Base64 encoded (encrypted storage recommended)
}

impl DeviceKey {
    /// Export as serializable key pair
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
    pub fn from_key_pair(pair: &KeyPair) -> Result<Self> {
        use base64::{engine::general_purpose::STANDARD, Engine};

        let private_bytes = STANDARD
            .decode(&pair.private_key)
            .map_err(|e| Error::Auth(format!("Invalid private key encoding: {}", e)))?;

        if private_bytes.len() != 32 {
            return Err(Error::Auth("Invalid private key length".to_string()));
        }

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
