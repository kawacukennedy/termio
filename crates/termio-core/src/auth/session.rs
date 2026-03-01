//! Session management
//!
//! JWT-based session tokens for API authentication.
//!
//! # Overview
//!
//! This module implements stateless JWT authentication for TERMIO.
//! Sessions are created when users authenticate and verified on each request.
//!
//! # JWT Structure
//!
//! ```json
//! {
//!   "sub": "user-uuid",
//!   "device_id": "device-uuid", 
//!   "exp": 1699999999,
//!   "iat": 1699900000,
//!   "scopes": ["read", "write", "execute"]
//! }
//! ```
//!
//! # Usage
//!
//! ```rust
//! use termio_core::auth::SessionManager;
//! use chrono::Duration;
//! use uuid::Uuid;
//!
//! let manager = SessionManager::new(secret.as_bytes());
//! let session = manager.create_session(
//!     user_id,
//!     device_id,
//!     Duration::hours(24),
//!     vec!["read".to_string()]
//! )?;
//!
//! // Later, verify the token
//! let claims = manager.verify_token(&session.token.0)?;
//! ```

use chrono::{Duration, Utc};
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::error::{Error, Result};

/// Session claims for JWT
///
/// This is the payload stored inside the JWT token.
/// Contains identity information and authorization scope.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Claims {
    /// Subject (User ID) - who this token represents
    pub sub: String,
    
    /// Device ID - which device this token is for
    pub device_id: String,
    
    /// Expiration time - Unix timestamp when token expires
    pub exp: usize,
    
    /// Issued at - Unix timestamp when token was created
    pub iat: usize,
    
    /// Permissions/Scopes - what this token allows
    /// e.g., ["read", "write", "execute_plugin"]
    pub scopes: Vec<String>,
}

/// Opaque session token
///
/// Wrapper around the JWT string to prevent accidental string operations
/// and make the API clearer.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Token(pub String);

impl fmt::Display for Token {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

use std::fmt;

/// Session manager
///
/// Creates and verifies JWT session tokens.
/// Each instance uses a single secret key for all operations.
pub struct SessionManager {
    /// Key for encoding new tokens
    encoding_key: EncodingKey,
    /// Key for decoding/verifying tokens
    decoding_key: DecodingKey,
}

impl SessionManager {
    /// Create a new session manager with a secret
    ///
    /// The secret should be at least 32 bytes and stored securely.
    /// In production, load from environment or secure storage.
    ///
    /// # Arguments
    ///
    /// * `secret` - Secret key for signing tokens (min 32 bytes recommended)
    pub fn new(secret: &[u8]) -> Self {
        Self {
            encoding_key: EncodingKey::from_secret(secret),
            decoding_key: DecodingKey::from_secret(secret),
        }
    }

    /// Create a new session for a user on a device
    ///
    /// Generates a JWT token with the user's ID, device ID,
    /// expiration time, and requested permissions.
    ///
    /// # Arguments
    ///
    /// * `user_id` - The user's UUID
    /// * `device_id` - The device's UUID  
    /// * `duration` - How long the session lasts
    /// * `scopes` - Permission scopes for this session
    ///
    /// # Returns
    ///
    /// A Session containing the JWT token and metadata
    ///
    /// # Example
    ///
    /// ```rust
    /// use chrono::Duration;
    /// use uuid::Uuid;
    ///
    /// let session = manager.create_session(
    ///     Uuid::new_v4(),
    ///     Uuid::new_v4(),
    ///     Duration::hours(24),
    ///     vec!["read".to_string(), "write".to_string()]
    /// )?;
    /// ```
    pub fn create_session(
        &self,
        user_id: Uuid,
        device_id: Uuid,
        duration: Duration,
        scopes: Vec<String>,
    ) -> Result<Session> {
        let now = Utc::now();
        let expires_at = now + duration;

        // Build JWT claims
        let claims = Claims {
            sub: user_id.to_string(),
            device_id: device_id.to_string(),
            exp: expires_at.timestamp() as usize,
            iat: now.timestamp() as usize,
            scopes,
        };

        // Sign the token
        let token_str = encode(&Header::default(), &claims, &self.encoding_key)
            .map_err(|e| Error::Auth(format!("Token generation failed: {}", e)))?;

        Ok(Session {
            token: Token(token_str),
            user_id,
            device_id,
            expires_at: expires_at.timestamp(),
        })
    }

    /// Verify a session token
    ///
    /// Decodes and validates the JWT token.
    /// Checks signature and expiration.
    ///
    /// # Arguments
    ///
    /// * `token` - The JWT string to verify
    ///
    /// # Returns
    ///
    /// The Claims if valid, error if invalid/expired
    ///
    /// # Example
    ///
    /// ```rust
    /// match manager.verify_token(&token_str) {
    ///     Ok(claims) => println!("User: {}", claims.sub),
    ///     Err(e) => println!("Invalid token: {}", e),
    /// }
    /// ```
    pub fn verify_token(&self, token: &str) -> Result<Claims> {
        let mut validation = Validation::default();
        validation.validate_exp = true;  // Reject expired tokens

        let token_data = decode::<Claims>(token, &self.decoding_key, &validation)
            .map_err(|e| Error::Auth(format!("Invalid token: {}", e)))?;

        Ok(token_data.claims)
    }
}

/// Active session
///
/// Contains the token and associated metadata.
/// Returned when creating a new session.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    /// The JWT token string
    pub token: Token,
    /// User ID from the token
    pub user_id: Uuid,
    /// Device ID from the token
    pub device_id: Uuid,
    /// When the session expires (Unix timestamp)
    pub expires_at: i64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_session_creation_verification() {
        let secret = b"super_secret_key";
        let manager = SessionManager::new(secret);

        let user_id = Uuid::new_v4();
        let device_id = Uuid::new_v4();

        let session = manager
            .create_session(
                user_id,
                device_id,
                Duration::hours(1),
                vec!["read".to_string()],
            )
            .unwrap();

        let claims = manager.verify_token(&session.token.0).unwrap();

        assert_eq!(claims.sub, user_id.to_string());
        assert_eq!(claims.device_id, device_id.to_string());
        assert_eq!(claims.scopes, vec!["read".to_string()]);
    }

    #[test]
    fn test_expired_token() {
        use jsonwebtoken::{encode, Header};

        let secret = b"secret";
        let manager = SessionManager::new(secret);

        // Create an expired token directly (expired 1 hour ago)
        let expired_claims = Claims {
            sub: Uuid::new_v4().to_string(),
            device_id: Uuid::new_v4().to_string(),
            exp: (Utc::now() - Duration::hours(1)).timestamp() as usize,
            iat: (Utc::now() - Duration::hours(1)).timestamp() as usize,
            scopes: vec![],
        };

        let token = encode(&Header::default(), &expired_claims, &manager.encoding_key).unwrap();

        let result = manager.verify_token(&token);
        assert!(
            result.is_err(),
            "Expected expired token to fail verification, got: {:?}",
            result
        );
    }
}
