//! Audit logging middleware
//!
//! Captures immutable audit trail for HIPAA compliance.
//! Logs: timestamp, user, endpoint, method, status code, duration.

use std::time::Instant;

use axum::{
    extract::Request,
    middleware::Next,
    response::Response,
};

/// Audit logging middleware
///
/// Logs every request with structured tracing fields for
/// HIPAA-compliant immutable audit trail.
pub async fn audit_middleware(
    request: Request,
    next: Next,
) -> Response {
    let start = Instant::now();
    let method = request.method().clone();
    let uri = request.uri().path().to_string();
    let version = format!("{:?}", request.version());

    // Extract user info from extensions if available (set by auth middleware)
    let user_id = request
        .headers()
        .get("x-user-id")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("anonymous")
        .to_string();

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

    // Execute the request
    let response = next.run(request).await;

    let duration = start.elapsed();
    let status = response.status().as_u16();

    // Structured audit log entry
    tracing::info!(
        target: "audit",
        method = %method,
        uri = %uri,
        status = status,
        duration_ms = duration.as_millis() as u64,
        user_id = %user_id,
        client_ip = %client_ip,
        http_version = %version,
        "API request"
    );

    // Log elevated events separately for security monitoring
    if status >= 400 {
        tracing::warn!(
            target: "security",
            method = %method,
            uri = %uri,
            status = status,
            user_id = %user_id,
            client_ip = %client_ip,
            "Elevated security event"
        );
    }

    response
}
