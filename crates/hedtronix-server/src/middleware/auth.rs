//! Authentication middleware
//!
//! Checks session tokens for API requests.

use axum::{
    extract::{Request, State},
    http::{StatusCode, header},
    middleware::Next,
    response::Response,
};
use hedtronix_core::auth::SessionManager;
use std::sync::Arc;

use crate::state::AppState;

/// Authentication middleware
pub async fn auth_middleware(
    State(state): State<AppState>,
    mut request: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    // Basic implementation - verify token from Authorization header
    let auth_header = request
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|value| value.to_str().ok())
        .ok_or(StatusCode::UNAUTHORIZED)?;

    if !auth_header.starts_with("Bearer ") {
        return Err(StatusCode::UNAUTHORIZED);
    }

    let token = &auth_header[7..];

    // In a real app we would use a proper session manager from state
    // For now we just check if token is present
    if token.is_empty() {
        return Err(StatusCode::UNAUTHORIZED);
    }

    Ok(next.run(request).await)
}
