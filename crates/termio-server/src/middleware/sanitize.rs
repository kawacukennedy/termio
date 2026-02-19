//! Input sanitization middleware
//!
//! Validates request body size limits and strips potentially dangerous content.

use axum::{
    body::{to_bytes, Body},
    extract::Request,
    http::StatusCode,
    middleware::Next,
    response::{IntoResponse, Response},
};

/// Maximum request body size (1MB)
const MAX_BODY_SIZE: usize = 1_048_576;

/// Input sanitization middleware
///
/// Enforces request body size limits and basic content safety checks.
/// Rejects requests that exceed the size limit.
pub async fn sanitize_middleware(
    request: Request,
    next: Next,
) -> Result<Response, Response> {
    // Check Content-Length header if present
    if let Some(content_length) = request
        .headers()
        .get(axum::http::header::CONTENT_LENGTH)
        .and_then(|v| v.to_str().ok())
        .and_then(|v| v.parse::<usize>().ok())
    {
        if content_length > MAX_BODY_SIZE {
            return Err((
                StatusCode::PAYLOAD_TOO_LARGE,
                "Request body too large",
            )
                .into_response());
        }
    }

    // For POST/PUT/PATCH requests, read and validate the body
    let method = request.method().clone();
    if matches!(
        method,
        axum::http::Method::POST | axum::http::Method::PUT | axum::http::Method::PATCH
    ) {
        let (parts, body) = request.into_parts();

        // Read body bytes with size limit
        match to_bytes(body, MAX_BODY_SIZE).await {
            Ok(bytes) => {
                let sanitized = sanitize_bytes(&bytes);
                let new_request =
                    Request::from_parts(parts, Body::from(sanitized));
                Ok(next.run(new_request).await)
            }
            Err(_) => Err((
                StatusCode::PAYLOAD_TOO_LARGE,
                "Request body exceeds maximum size",
            )
                .into_response()),
        }
    } else {
        Ok(next.run(request).await)
    }
}

/// Sanitize request body bytes
///
/// For JSON payloads, strip potentially dangerous patterns.
fn sanitize_bytes(bytes: &[u8]) -> Vec<u8> {
    let Ok(text) = std::str::from_utf8(bytes) else {
        return bytes.to_vec();
    };

    // Remove dangerous HTML/script patterns from string values
    let sanitized = text
        .replace("<script", "&lt;script")
        .replace("</script", "&lt;/script")
        .replace("javascript:", "")
        .replace("onerror=", "")
        .replace("onload=", "");

    sanitized.into_bytes()
}
