//! AES-256-GCM encryption
//!
//! Provides authenticated encryption for data at rest.
//!
//! # Algorithm Details
//!
//! - **Cipher**: AES-256 in GCM mode
//! - **Nonce**: 12 bytes (96 bits), randomly generated each encryption
//! - **Tag**: 16 bytes (128 bits), authentication tag
//!
//! # Security Properties
//!
//! - **Confidentiality**: AES-256 provides strong confidentiality
//! - **Integrity**: GCM mode includes authentication tag
//! - **Nonce uniqueness**: Each encryption generates fresh random nonce
//!
//! # Usage
//!
//! ```rust
//! use termio_core::crypto::{encrypt, decrypt, EncryptedData};
//!
//! let key = [0u8; 32];  // Must be exactly 32 bytes
//!
//! // Encrypt plaintext
//! let encrypted = encrypt(&key, b"Hello TERMIO")?;
//!
//! // Decrypt ciphertext
//! let plaintext = decrypt(&key, &encrypted)?;
//! assert_eq!(plaintext, b"Hello TERMIO");
//!
//! // Serialize for storage
//! let encoded = encrypted.to_base64();
//! let restored = EncryptedData::from_base64(&encoded)?;
//! ```

use aes_gcm::{
    aead::{Aead, KeyInit, OsRng},
    Aes256Gcm, Key, Nonce,
};
use rand::RngCore;
use serde::{Deserialize, Serialize};

use crate::error::{Error, Result};

/// Encrypted data with nonce
///
/// Contains all components needed for decryption:
/// - Nonce: Random 12-byte IV
/// - Ciphertext: Encrypted data + 16-byte authentication tag
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncryptedData {
    /// 12-byte nonce (initialization vector)
    /// Must be unique per encryption with same key
    pub nonce: Vec<u8>,
    
    /// Encrypted ciphertext with 16-byte authentication tag appended
    /// Tag is at the end of the vec
    pub ciphertext: Vec<u8>,
}

impl EncryptedData {
    /// Encode to base64 string
    ///
    /// Convenience method for storage/transmission.
    /// Combines nonce and ciphertext into single string.
    ///
    /// # Returns
    ///
    /// Base64-encoded string: nonce || ciphertext
    pub fn to_base64(&self) -> String {
        use base64::Engine;
        let mut combined = self.nonce.clone();
        combined.extend(&self.ciphertext);
        base64::engine::general_purpose::STANDARD.encode(&combined)
    }

    /// Decode from base64 string
    ///
    /// Inverse of to_base64().
    ///
    /// # Arguments
    ///
    /// * `s` - Base64-encoded nonce || ciphertext
    ///
    /// # Returns
    ///
    /// EncryptedData with parsed nonce and ciphertext
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
///
/// Uses GCM (Galois/Counter Mode) for authenticated encryption.
/// Each call generates a fresh random nonce.
///
/// # Arguments
///
/// * `key` - 32-byte encryption key
/// * `plaintext` - Data to encrypt
///
/// # Returns
///
/// EncryptedData containing nonce and ciphertext
///
/// # Example
///
/// ```rust
/// let key = [0u8; 32];
/// let encrypted = encrypt(&key, b"secret").unwrap();
/// assert_eq!(encrypted.nonce.len(), 12);
/// ```
pub fn encrypt(key: &[u8; 32], plaintext: &[u8]) -> Result<EncryptedData> {
    // Create cipher from key
    let key = Key::<Aes256Gcm>::from_slice(key);
    let cipher = Aes256Gcm::new(key);

    // Generate random 12-byte nonce
    let mut nonce_bytes = [0u8; 12];
    OsRng.fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);

    // Encrypt with GCM (includes authentication tag)
    let ciphertext = cipher
        .encrypt(nonce, plaintext)
        .map_err(|e| Error::Encryption(format!("Encryption failed: {}", e)))?;

    Ok(EncryptedData {
        nonce: nonce_bytes.to_vec(),
        ciphertext,
    })
}

/// Decrypt data with AES-256-GCM
///
/// Verifies authentication tag before returning plaintext.
/// If tag verification fails, returns error without plaintext.
///
/// # Arguments
///
/// * `key` - 32-byte encryption key (same as used for encryption)
/// * `encrypted` - EncryptedData from encrypt()
///
/// # Returns
///
/// Decrypted plaintext bytes
///
/// # Example
///
/// ```rust
/// let key = [0u8; 32];
/// let encrypted = encrypt(&key, b"secret").unwrap();
/// let plaintext = decrypt(&key, &encrypted).unwrap();
/// assert_eq!(plaintext, b"secret");
/// ```
pub fn decrypt(key: &[u8; 32], encrypted: &EncryptedData) -> Result<Vec<u8>> {
    let key = Key::<Aes256Gcm>::from_slice(key);
    let cipher = Aes256Gcm::new(key);

    let nonce = Nonce::from_slice(&encrypted.nonce);

    // Decrypt and verify authentication tag
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
        let plaintext = b"Hello, TERMIO!";

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
