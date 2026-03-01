//! Argon2id key derivation
//!
//! Secure password-based key derivation for encryption.
//!
//! # Algorithm
//!
//! Argon2id is the recommended Argon2 variant, combining:
//! - **Data-dependent**: Memory-hard for password hashing
//! - **Data-independent**: Resistant to GPU cracking
//!
//! # Parameters (per OWASP recommendations)
//!
//! - **Memory**: 64 MB (65536 KB)
//! - **Time**: 3 iterations
//! - **Parallelism**: 4 threads
//! - **Output**: 32 bytes (256 bits)
//!
//! # Usage
//!
//! ```rust
//! use termio_core::crypto::{derive_key, verify_password};
//!
//! // Derive key from password
//! let derived = derive_key("my_secure_password", None).unwrap();
//! assert_eq!(derived.key.len(), 32);
//!
//! // Later, verify password
//! assert!(verify_password("my_secure_password", &derived).unwrap());
//! assert!(!verify_password("wrong_password", &derived).unwrap());
//! ```

use argon2::{
    password_hash::{PasswordHasher, SaltString},
    Argon2, Params,
};
use rand::rngs::OsRng;
use serde::{Deserialize, Serialize};

use crate::error::{Error, Result};

/// Derived key with salt for storage
///
/// Contains the derived key bytes and the salt used.
/// The salt should be stored alongside the key.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DerivedKey {
    /// 32-byte derived key (256 bits)
    pub key: [u8; 32],
    /// Salt used for derivation (Base64 encoded)
    pub salt: String,
}

/// Derive a key from a password using Argon2id
///
/// Uses secure parameters optimized for password hashing:
/// - Memory: 64 MB
/// - Time: 3 iterations
/// - Parallelism: 4
///
/// # Arguments
///
/// * `password` - User's password (can be any length)
/// * `salt` - Optional salt. If None, generates random salt.
///
/// # Returns
///
/// DerivedKey containing 32-byte key and salt
///
/// # Example
///
/// ```rust
/// let derived = derive_key("password123", None).unwrap();
/// println!("Key: {:02x?}", derived.key);
/// println!("Salt: {}", derived.salt);
/// ```
pub fn derive_key(password: &str, salt: Option<&str>) -> Result<DerivedKey> {
    // Generate or use provided salt
    let salt_string = match salt {
        Some(s) => SaltString::from_b64(s)
            .map_err(|e| Error::Encryption(format!("Invalid salt: {}", e)))?,
        None => SaltString::generate(&mut OsRng),
    };

    // Configure Argon2id with secure parameters per OWASP
    // Memory: 64 MB, Time: 3 iterations, Parallelism: 4
    let params = Params::new(
        64 * 1024, // memory cost (64 MiB)
        3,         // time cost (iterations)
        4,         // parallelism
        Some(32),  // output length (32 bytes = 256 bits)
    )
    .map_err(|e| Error::Encryption(format!("Invalid params: {}", e)))?;

    let argon2 = Argon2::new(argon2::Algorithm::Argon2id, argon2::Version::V0x13, params);

    // Derive key from password
    let hash = argon2
        .hash_password(password.as_bytes(), &salt_string)
        .map_err(|e| Error::Encryption(format!("Key derivation failed: {}", e)))?;

    // Extract raw hash bytes
    let hash_bytes = hash
        .hash
        .ok_or_else(|| Error::Encryption("No hash output".to_string()))?;

    let hash_slice = hash_bytes.as_bytes();
    if hash_slice.len() < 32 {
        return Err(Error::Encryption("Hash too short".to_string()));
    }

    // Copy to fixed-size array
    let mut key = [0u8; 32];
    key.copy_from_slice(&hash_slice[..32]);

    Ok(DerivedKey {
        key,
        salt: salt_string.to_string(),
    })
}

/// Verify a password against a stored key
///
/// Re-derives the key with the stored salt and compares.
///
/// # Arguments
///
/// * `password` - Password to verify
/// * `stored` - Previously derived key with salt
///
/// # Returns
///
/// true if password matches, false otherwise
pub fn verify_password(password: &str, stored: &DerivedKey) -> Result<bool> {
    let derived = derive_key(password, Some(&stored.salt))?;
    Ok(derived.key == stored.key)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_derive_key() {
        let password = "test_password_123";
        let derived = derive_key(password, None).unwrap();

        assert_eq!(derived.key.len(), 32);
        assert!(!derived.salt.is_empty());
    }

    #[test]
    fn test_deterministic_with_salt() {
        let password = "same_password";
        
        // Same salt = same derived key
        let derived1 = derive_key(password, None).unwrap();
        let derived2 = derive_key(password, Some(&derived1.salt)).unwrap();

        assert_eq!(derived1.key, derived2.key);
    }

    #[test]
    fn test_different_passwords_different_keys() {
        let derived1 = derive_key("password1", None).unwrap();
        let derived2 = derive_key("password2", Some(&derived1.salt)).unwrap();

        assert_ne!(derived1.key, derived2.key);
    }

    #[test]
    fn test_verify_password() {
        let password = "verify_me";
        let stored = derive_key(password, None).unwrap();

        assert!(verify_password(password, &stored).unwrap());
        assert!(!verify_password("wrong_password", &stored).unwrap());
    }
}
