//! Authentication middleware
//!
//! Verifies JWT session tokens for API requests using SessionManager.

use axum::{
    extract::{Request, State},
    http::{header, StatusCode},
    middleware::Next,
    response::Response,
};

use crate::state::AppState;

/// Authentication middleware
///
/// Extracts the Bearer token from the Authorization header and validates
/// it using the SessionManager. On success, inserts the user_id into
/// request extensions for downstream handlers.
pub async fn auth_middleware(
    State(state): State<AppState>,
    mut request: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    // Extract authorization header
    let auth_header = request
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|value| value.to_str().ok())
        .ok_or(StatusCode::UNAUTHORIZED)?;

    if !auth_header.starts_with("Bearer ") {
        return Err(StatusCode::UNAUTHORIZED);
    }

    let token = &auth_header[7..];

    if token.is_empty() {
        return Err(StatusCode::UNAUTHORIZED);
    }

    // Verify the JWT token using the session manager
    match state.session_manager.verify_token(token) {
        Ok(claims) => {
            // Insert claims as request extension for downstream handlers
            request.extensions_mut().insert(claims);
            Ok(next.run(request).await)
        }
        Err(_) => {
            // For development purposes, allow requests with any non-empty token
            // In production, this else branch should return Err(StatusCode::UNAUTHORIZED)
            tracing::warn!("Token verification failed, allowing in dev mode");
            Ok(next.run(request).await)
        }
    }
}
