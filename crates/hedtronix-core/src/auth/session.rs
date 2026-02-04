//! Session management
//!
//! JWT-based session tokens for API authentication.

use chrono::{Duration, Utc};
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::error::{Error, Result};

/// Session claims for JWT
#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    /// Subject (User ID)
    pub sub: String,
    /// Device ID
    pub device_id: String,
    /// Expiration time
    pub exp: usize,
    /// Issued at
    pub iat: usize,
    /// Permissions/Scopes
    pub scopes: Vec<String>,
}

/// Opaque session token
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Token(pub String);

impl fmt::Display for Token {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

use std::fmt;

/// Session manager
pub struct SessionManager {
    encoding_key: EncodingKey,
    decoding_key: DecodingKey,
}

impl SessionManager {
    /// Create a new session manager with a secret
    pub fn new(secret: &[u8]) -> Self {
        Self {
            encoding_key: EncodingKey::from_secret(secret),
            decoding_key: DecodingKey::from_secret(secret),
        }
    }

    /// Create a new session for a user on a device
    pub fn create_session(
        &self,
        user_id: Uuid,
        device_id: Uuid,
        duration: Duration,
        scopes: Vec<String>,
    ) -> Result<Session> {
        let now = Utc::now();
        let expires_at = now + duration;

        let claims = Claims {
            sub: user_id.to_string(),
            device_id: device_id.to_string(),
            exp: expires_at.timestamp() as usize,
            iat: now.timestamp() as usize,
            scopes,
        };

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
    pub fn verify_token(&self, token: &str) -> Result<Claims> {
        let token_data = decode::<Claims>(
            token,
            &self.decoding_key,
            &Validation::default(),
        )
        .map_err(|e| Error::Auth(format!("Invalid token: {}", e)))?;

        Ok(token_data.claims)
    }
}

/// Active session
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    pub token: Token,
    pub user_id: Uuid,
    pub device_id: Uuid,
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
        
        let session = manager.create_session(
            user_id,
            device_id,
            Duration::hours(1),
            vec!["read".to_string()]
        ).unwrap();
        
        let claims = manager.verify_token(&session.token.0).unwrap();
        
        assert_eq!(claims.sub, user_id.to_string());
        assert_eq!(claims.device_id, device_id.to_string());
        assert_eq!(claims.scopes, vec!["read".to_string()]);
    }

    #[test]
    fn test_expired_token() {
        let secret = b"secret";
        let manager = SessionManager::new(secret);
        
        // Create expired session (1 second ago)
        let session = manager.create_session(
            Uuid::new_v4(),
            Uuid::new_v4(),
            Duration::seconds(-1), 
            vec![]
        ).unwrap();
        
        let result = manager.verify_token(&session.token.0);
        assert!(result.is_err());
    }
}
