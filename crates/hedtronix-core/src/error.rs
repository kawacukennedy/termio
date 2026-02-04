//! Error types for HEDTRONIX
//!
//! Follows the error categorization from the specification:
//! - User errors (4000-4099): Invalid input, insufficient permissions
//! - System errors (5000-5099): Database issues, memory allocation
//! - AI errors (6000-6099): Model load failures, inference timeouts
//! - Network errors (7000-7099): Offline, timeouts, rate limiting

use thiserror::Error;

/// Result type alias using the HEDTRONIX Error type
pub type Result<T> = std::result::Result<T, Error>;

/// HEDTRONIX error types
#[derive(Error, Debug)]
pub enum Error {
    // User Errors (4000-4099)
    #[error("Invalid input: {0}")]
    InvalidInput(String),

    #[error("Insufficient permissions: {0}")]
    InsufficientPermissions(String),

    #[error("Quota exceeded: {0}")]
    QuotaExceeded(String),

    // System Errors (5000-5099)
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Configuration error: {0}")]
    Config(#[from] config::ConfigError),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    #[error("Internal error: {0}")]
    Internal(String),

    // AI Errors (6000-6099)
    #[error("Model load failed: {0}")]
    ModelLoadFailed(String),

    #[error("Inference timeout after {0}ms")]
    InferenceTimeout(u64),

    #[error("Context overflow: token count {0} exceeds limit {1}")]
    ContextOverflow(usize, usize),

    // Network Errors (7000-7099)
    #[error("Network unavailable")]
    NetworkUnavailable,

    #[error("Request timeout")]
    RequestTimeout,

    #[error("Rate limited: retry after {0} seconds")]
    RateLimited(u64),
}

impl Error {
    /// Get the error code for categorization
    pub fn code(&self) -> u16 {
        match self {
            // User errors
            Error::InvalidInput(_) => 4000,
            Error::InsufficientPermissions(_) => 4001,
            Error::QuotaExceeded(_) => 4002,

            // System errors
            Error::Database(_) => 5000,
            Error::Config(_) => 5001,
            Error::Io(_) => 5002,
            Error::Serialization(_) => 5003,
            Error::Internal(_) => 5099,

            // AI errors
            Error::ModelLoadFailed(_) => 6000,
            Error::InferenceTimeout(_) => 6001,
            Error::ContextOverflow(_, _) => 6002,

            // Network errors
            Error::NetworkUnavailable => 7000,
            Error::RequestTimeout => 7001,
            Error::RateLimited(_) => 7002,
        }
    }

    /// Check if this is a retryable error
    pub fn is_retryable(&self) -> bool {
        matches!(
            self,
            Error::Database(_)
                | Error::NetworkUnavailable
                | Error::RequestTimeout
                | Error::RateLimited(_)
                | Error::InferenceTimeout(_)
        )
    }
}
