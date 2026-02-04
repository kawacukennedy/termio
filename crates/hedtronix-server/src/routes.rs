//! Route definitions

use axum::{routing::get, routing::post, Router};

use crate::handlers;
use crate::state::AppState;

/// Health check routes
pub fn health_routes() -> Router<AppState> {
    Router::new().route("/health", get(handlers::health_check))
}

/// Conversation routes
pub fn conversation_routes() -> Router<AppState> {
    Router::new()
        .route("/api/conversations", get(handlers::list_conversations))
        .route("/api/conversations", post(handlers::create_conversation))
        .route(
            "/api/conversations/:id",
            get(handlers::get_conversation),
        )
        .route(
            "/api/conversations/:id/messages",
            post(handlers::add_message),
        )
}

/// Memory routes
pub fn memory_routes() -> Router<AppState> {
    Router::new()
        .route("/api/memory", get(handlers::search_memory))
        .route("/api/memory", post(handlers::create_memory_entry))
}

/// AI routes
pub fn ai_routes() -> Router<AppState> {
    Router::new()
        .route("/api/ai/chat", post(handlers::chat))
        .route("/api/ai/status", get(handlers::ai_status))
}
