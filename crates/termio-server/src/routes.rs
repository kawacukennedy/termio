//! Route definitions

use axum::{
    routing::{delete, get, patch, post, put},
    Router,
};

use crate::handlers;
use crate::state::AppState;

/// Health check routes (public, no auth)
pub fn health_routes() -> Router<AppState> {
    Router::new()
        .route("/health", get(handlers::health_check))
        .route("/api/health", get(handlers::system_health))
}

/// Conversation routes (requires auth)
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

/// Memory routes (requires auth)
pub fn memory_routes() -> Router<AppState> {
    Router::new()
        .route("/api/memory", get(handlers::search_memory))
        .route("/api/memory", post(handlers::create_memory_entry))
}

/// AI routes (requires auth)
pub fn ai_routes() -> Router<AppState> {
    Router::new()
        .route("/api/ai/chat", post(handlers::chat))
        .route("/api/ai/status", get(handlers::ai_status))
}

/// Notification routes (requires auth)
pub fn notification_routes() -> Router<AppState> {
    Router::new()
        .route("/api/notifications", get(handlers::list_notifications))
        .route(
            "/api/notifications/:id/dismiss",
            put(handlers::dismiss_notification),
        )
        .route(
            "/api/notifications/:id/read",
            put(handlers::mark_notification_read),
        )
}

/// Sync routes (requires auth)
pub fn sync_routes() -> Router<AppState> {
    Router::new()
        .route("/api/sync/status", get(handlers::sync_status))
        .route("/api/sync/trigger", post(handlers::trigger_sync))
}

/// Plugin routes (requires auth)
pub fn plugin_routes() -> Router<AppState> {
    Router::new()
        .route("/api/plugins", get(handlers::list_plugins))
        .route("/api/plugins", post(handlers::install_plugin))
        .route("/api/plugins/:id/toggle", patch(handlers::toggle_plugin))
        .route("/api/plugins/:id", delete(handlers::uninstall_plugin))
}

/// Knowledge graph routes (FA-003, requires auth)
pub fn knowledge_graph_routes() -> Router<AppState> {
    Router::new()
        .route("/api/knowledge", get(handlers::query_knowledge_graph))
        .route("/api/knowledge/nodes", post(handlers::create_knowledge_node))
        .route("/api/knowledge/edges", post(handlers::create_knowledge_edge))
}

/// Health data routes (FA-008, requires auth)
pub fn health_data_routes() -> Router<AppState> {
    Router::new()
        .route("/api/health-data", get(handlers::list_health_data))
        .route("/api/health-data", post(handlers::create_health_data))
}

/// Action plan routes (FA-002 Agentic, requires auth)
pub fn action_plan_routes() -> Router<AppState> {
    Router::new()
        .route("/api/action-plans", get(handlers::list_action_plans))
        .route("/api/action-plans", post(handlers::create_action_plan))
        .route("/api/action-plans/:id/approve", put(handlers::approve_action_plan))
        .route("/api/action-plans/:id/execute", post(handlers::execute_action_plan_step))
}
