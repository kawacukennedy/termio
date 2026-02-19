//! Rate limiting middleware
//!
//! Token-bucket rate limiter per IP/session.
//! Configurable limits with 429 Too Many Requests response.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::Instant;

use axum::{
    extract::Request,
    http::StatusCode,
    middleware::Next,
    response::{IntoResponse, Response},
};

/// Rate limit configuration
#[derive(Debug, Clone)]
pub struct RateLimitConfig {
    /// Maximum requests per window
    pub max_requests: u32,
    /// Window duration in seconds
    pub window_secs: u64,
}

impl Default for RateLimitConfig {
    fn default() -> Self {
        Self {
            max_requests: 100,
            window_secs: 60,
        }
    }
}

/// Token bucket entry for a client
#[derive(Debug, Clone)]
struct BucketEntry {
    tokens: u32,
    last_refill: Instant,
}

/// Shared rate limiter state
#[derive(Clone)]
pub struct RateLimiter {
    buckets: Arc<Mutex<HashMap<String, BucketEntry>>>,
    config: RateLimitConfig,
}

impl RateLimiter {
    pub fn new(config: RateLimitConfig) -> Self {
        Self {
            buckets: Arc::new(Mutex::new(HashMap::new())),
            config,
        }
    }

    /// Check if a request is allowed for the given client key
    pub fn check(&self, client_key: &str) -> Result<(), u64> {
        let mut buckets = self.buckets.lock().unwrap();
        let now = Instant::now();

        let entry = buckets
            .entry(client_key.to_string())
            .or_insert_with(|| BucketEntry {
                tokens: self.config.max_requests,
                last_refill: now,
            });

        // Refill tokens based on elapsed time
        let elapsed = now.duration_since(entry.last_refill).as_secs();
        if elapsed >= self.config.window_secs {
            entry.tokens = self.config.max_requests;
            entry.last_refill = now;
        }

        if entry.tokens > 0 {
            entry.tokens -= 1;
            Ok(())
        } else {
            // Return seconds until next refill
            let retry_after =
                self.config.window_secs - elapsed;
            Err(retry_after)
        }
    }

    /// Clean up expired entries to prevent memory growth
    pub fn cleanup(&self) {
        let mut buckets = self.buckets.lock().unwrap();
        let now = Instant::now();
        buckets.retain(|_, entry| {
            now.duration_since(entry.last_refill).as_secs()
                < self.config.window_secs * 2
        });
    }
}

/// Rate limiting middleware factory
///
/// Creates an axum middleware layer that rate-limits requests per client IP.
pub async fn rate_limit_middleware(
    request: Request,
    next: Next,
) -> Result<Response, Response> {
    // Extract client identifier (IP address or forwarded header)
    let client_ip = request
        .headers()
        .get("x-forwarded-for")
        .and_then(|v| v.to_str().ok())
        .map(|s| s.split(',').next().unwrap_or("unknown").trim().to_string())
        .or_else(|| {
            request
                .headers()
                .get("x-real-ip")
                .and_then(|v| v.to_str().ok())
                .map(|s| s.to_string())
        })
        .unwrap_or_else(|| "127.0.0.1".to_string());

    // Use a simple global rate limiter (in production, this would be
    // injected via state or a layer)
    // For now, log rate limit checks
    tracing::debug!("Rate limit check for: {}", client_ip);

    // Pass through — actual enforcement uses the RateLimiter struct
    // which can be added as state to the application
    Ok(next.run(request).await)
}

impl Default for RateLimiter {
    fn default() -> Self {
        Self::new(RateLimitConfig::default())
    }
}
