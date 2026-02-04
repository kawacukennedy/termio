//! AES-256-GCM encryption
//!
//! Provides authenticated encryption for data at rest.

use aes_gcm::{
    aead::{Aead, KeyInit, OsRng},
    Aes256Gcm, Key, Nonce,
};
use rand::RngCore;
use serde::{Deserialize, Serialize};

use crate::error::{Error, Result};

/// Encrypted data with nonce
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncryptedData {
    /// 12-byte nonce
    pub nonce: Vec<u8>,
    /// Encrypted ciphertext with authentication tag
    pub ciphertext: Vec<u8>,
}

impl EncryptedData {
    /// Encode to base64 string
    pub fn to_base64(&self) -> String {
        use base64::Engine;
        let mut combined = self.nonce.clone();
        combined.extend(&self.ciphertext);
        base64::engine::general_purpose::STANDARD.encode(&combined)
    }

    /// Decode from base64 string
    pub fn from_base64(s: &str) -> Result<Self> {
        use base64::Engine;
        let bytes = base64::engine::general_purpose::STANDARD
            .decode(s)
            .map_err(|e| Error::Encryption(format!("Invalid base64: {}", e)))?;

        if bytes.len() < 12 {
            return Err(Error::Encryption("Data too short".to_string()));
        }

        Ok(Self {
            nonce: bytes[..12].to_vec(),
            ciphertext: bytes[12..].to_vec(),
        })
    }
}

/// Encrypt data with AES-256-GCM
pub fn encrypt(key: &[u8; 32], plaintext: &[u8]) -> Result<EncryptedData> {
    let key = Key::<Aes256Gcm>::from_slice(key);
    let cipher = Aes256Gcm::new(key);

    // Generate random nonce
    let mut nonce_bytes = [0u8; 12];
    OsRng.fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);

    // Encrypt
    let ciphertext = cipher
        .encrypt(nonce, plaintext)
        .map_err(|e| Error::Encryption(format!("Encryption failed: {}", e)))?;

    Ok(EncryptedData {
        nonce: nonce_bytes.to_vec(),
        ciphertext,
    })
}

/// Decrypt data with AES-256-GCM
pub fn decrypt(key: &[u8; 32], encrypted: &EncryptedData) -> Result<Vec<u8>> {
    let key = Key::<Aes256Gcm>::from_slice(key);
    let cipher = Aes256Gcm::new(key);

    let nonce = Nonce::from_slice(&encrypted.nonce);

    let plaintext = cipher
        .decrypt(nonce, encrypted.ciphertext.as_ref())
        .map_err(|e| Error::Encryption(format!("Decryption failed: {}", e)))?;

    Ok(plaintext)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_encrypt_decrypt() {
        let key = [0u8; 32];
        let plaintext = b"Hello, HEDTRONIX!";

        let encrypted = encrypt(&key, plaintext).unwrap();
        let decrypted = decrypt(&key, &encrypted).unwrap();

        assert_eq!(plaintext.as_slice(), decrypted.as_slice());
    }

    #[test]
    fn test_base64_roundtrip() {
        let key = [1u8; 32];
        let plaintext = b"Test data";

        let encrypted = encrypt(&key, plaintext).unwrap();
        let encoded = encrypted.to_base64();
        let decoded = EncryptedData::from_base64(&encoded).unwrap();
        let decrypted = decrypt(&key, &decoded).unwrap();

        assert_eq!(plaintext.as_slice(), decrypted.as_slice());
    }

    #[test]
    fn test_wrong_key_fails() {
        let key1 = [0u8; 32];
        let key2 = [1u8; 32];
        let plaintext = b"Secret";

        let encrypted = encrypt(&key1, plaintext).unwrap();
        let result = decrypt(&key2, &encrypted);

        assert!(result.is_err());
    }
}
