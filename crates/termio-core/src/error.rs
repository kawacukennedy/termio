//! Error types for TERMIO
//!
//! This module defines the centralized error handling system for TERMIO.
//! All errors are categorized with numeric codes for easy identification:
//!
//! - **User Errors (4000-4099)**: Invalid input, insufficient permissions, quota exceeded
//! - **System Errors (5000-5099)**: Database issues, memory allocation, configuration
//! - **AI Errors (6000-6099)**: Model load failures, inference timeouts, context overflow
//! - **Network Errors (7000-7099)**: Offline, timeouts, rate limiting
//!
//! # Error Code Reference
//!
//! | Code | Error Type | Description |
//! |------|-----------|-------------|
//! | 4000 | InvalidInput | User provided invalid input |
//! | 4001 | InsufficientPermissions | User lacks required permissions |
//! | 4002 | QuotaExceeded | User exceeded their quota |
//! | 5000 | Database | Database operation failed |
//! | 5001 | Config | Configuration error |
//! | 5002 | Io | File system or I/O error |
//! | 5003 | Serialization | JSON/serde error |
//! | 5050 | System | Internal system error |
//! | 5060 | Auth | Authentication error |
//! | 5070 | Encryption | Encryption/decryption error |
//! | 6000 | ModelLoadFailed | AI model failed to load |
//! | 6001 | InferenceTimeout | AI inference exceeded timeout |
//! | 6002 | ContextOverflow | Token count exceeds limit |
//! | 7000 | NetworkUnavailable | No network connection |
//! | 7001 | RequestTimeout | HTTP request timed out |
//! | 7002 | RateLimited | Too many requests, retry later |
//!
//! # Usage
//!
//! ```rust
//! use termio_core::error::{Error, Result};
//!
//! fn example() -> Result<String> {
//!     // Return an error with context
//!     Err(Error::InvalidInput("Name cannot be empty".to_string()))
//! }
//! ```

use thiserror::Error;

/// Result type alias using the TERMIO Error type
/// This is used throughout the codebase for consistent error handling
pub type Result<T> = std::result::Result<T, Error>;

/// TERMIO error types
///
/// All errors implement the `std::error::Error` trait via derive,
/// and include a numeric code for programmatic error handling.
/// Each variant wraps context information for debugging.
#[derive(Error, Debug)]
pub enum Error {
    // ========================================================================
    // User Errors (4000-4099) - Client-side issues that can be fixed by user
    // ========================================================================
    
    /// Invalid input: user provided data that failed validation
    /// Code: 4000
    #[error("Invalid input: {0}")]
    InvalidInput(String),

    /// Insufficient permissions: user lacks required capabilities
    /// Code: 4001
    #[error("Insufficient permissions: {0}")]
    InsufficientPermissions(String),

    /// Quota exceeded: user has hit their usage limit
    /// Code: 4002
    #[error("Quota exceeded: {0}")]
    QuotaExceeded(String),

    // ========================================================================
    // System Errors (5000-5099) - Internal issues that may require admin attention
    // ========================================================================
    
    /// Database error: SQLx database operation failed
    /// Code: 5000
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    /// Configuration error: config crate failed to load
    /// Code: 5001
    #[error("Configuration error: {0}")]
    Config(#[from] config::ConfigError),

    /// Configuration error: custom configuration validation failed
    /// Code: 5001
    #[error("Configuration error: {0}")]
    Configuration(String),

    /// I/O error: file system or standard I/O operation failed
    /// Code: 5002
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    /// Serialization error: JSON encoding/decoding failed
    /// Code: 5003
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    /// Internal error: unexpected internal failure
    /// Code: 5099
    #[error("Internal error: {0}")]
    Internal(String),

    /// System error: operating system or runtime error
    /// Code: 5050
    #[error("System error: {0}")]
    System(String),

    /// Authentication error: login, token, or credential failure
    /// Code: 5060
    #[error("Authentication error: {0}")]
    Auth(String),

    /// Encryption error: cryptographic operation failed
    /// Code: 5070
    #[error("Encryption error: {0}")]
    Encryption(String),

    // ========================================================================
    // AI Errors (6000-6099) - Issues related to AI/ML operations
    // ========================================================================
    
    /// Model load failed: AI model file not found or corrupted
    /// Code: 6000
    #[error("Model load failed: {0}")]
    ModelLoadFailed(String),

    /// Inference timeout: AI took too long to generate response
    /// Code: 6001
    #[error("Inference timeout after {0}ms")]
    InferenceTimeout(u64),

    /// Context overflow: conversation exceeds token limit
    /// Code: 6002
    #[error("Context overflow: token count {0} exceeds limit {1}")]
    ContextOverflow(usize, usize),

    // ========================================================================
    // Network Errors (7000-7099) - Connectivity and communication issues
    // ========================================================================
    
    /// Network unavailable: device is offline
    /// Code: 7000
    #[error("Network unavailable")]
    NetworkUnavailable,

    /// Request timeout: HTTP request exceeded timeout
    /// Code: 7001
    #[error("Request timeout")]
    RequestTimeout,

    /// Rate limited: too many requests, must retry after delay
    /// Code: 7002
    #[error("Rate limited: retry after {0} seconds")]
    RateLimited(u64),
}

impl Error {
    /// Get the error code for categorization
    ///
    /// Returns a numeric code that categorizes the error type:
    /// - 4000-4099: User errors
    /// - 5000-5099: System errors  
    /// - 6000-6099: AI errors
    /// - 7000-7099: Network errors
    ///
    /// # Example
    ///
    /// ```rust
    /// let err = Error::InvalidInput("invalid".to_string());
    /// assert_eq!(err.code(), 4000);
    /// ```
    pub fn code(&self) -> u16 {
        match self {
            // User errors (4000-4099)
            Error::InvalidInput(_) => 4000,
            Error::InsufficientPermissions(_) => 4001,
            Error::QuotaExceeded(_) => 4002,

            // System errors (5000-5099)
            Error::Database(_) => 5000,
            Error::Config(_) => 5001,
            Error::Configuration(_) => 5001,
            Error::Io(_) => 5002,
            Error::Serialization(_) => 5003,
            Error::Internal(_) => 5099,
            Error::System(_) => 5050,
            Error::Auth(_) => 5060,
            Error::Encryption(_) => 5070,

            // AI errors (6000-6099)
            Error::ModelLoadFailed(_) => 6000,
            Error::InferenceTimeout(_) => 6001,
            Error::ContextOverflow(_, _) => 6002,

            // Network errors (7000-7099)
            Error::NetworkUnavailable => 7000,
            Error::RequestTimeout => 7001,
            Error::RateLimited(_) => 7002,
        }
    }

    /// Check if this is a retryable error
    ///
    /// Returns true for transient errors that might succeed on retry:
    /// - Database errors
    /// - Network unavailable
    /// - Request timeouts
    /// - Rate limiting
    /// - Inference timeouts
    ///
    /// # Example
    ///
    /// ```rust
    /// let err = Error::NetworkUnavailable;
    /// if err.is_retryable() {
    ///     // Schedule retry with exponential backoff
    /// }
    /// ```
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
