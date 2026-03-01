//! TERMIO Backend Server
//!
//! Provides HTTP API for the AI assistant.
//!
//! # Overview
//!
//! The TERMIO server is built with Axum and provides RESTful APIs
//! for all client applications (TUI, mobile, desktop).
//!
//! # Features
//!
//! - **Authentication**: JWT-based session management
//! - **Rate Limiting**: Prevents abuse
//! - **Audit Logging**: Tracks all API requests
//! - **Health Checks**: /health and /api/health endpoints
//! - **CORS**: Configurable cross-origin support
//!
//! # Architecture
//!
//! ```text
//!                    ┌─────────────┐
//!                    │   Clients   │ (TUI, Mobile, Desktop)
//!                    └──────┬──────┘
//!                           │ HTTP
//!                           ▼
//!                    ┌─────────────┐
//!                    │   Axum     │  (Router + Middleware)
//!                    │  Server    │
//!                    └──────┬──────┘
//!                           │
////!         ┌─────────────────┼─────────────────┐
//!         ▼                 ▼                 ▼
//!    ┌─────────┐     ┌──────────┐     ┌─────────┐
//!    │ Routes │     │ Handlers │     │ State   │
//!    └─────────┘     └──────────┘     └─────────┘
//! ```
//!
//! # Running
//!
//! ```bash
//! cargo run -p termio-server
//! # Server starts on http://127.0.0.1:8080
//! ```

mod handlers;
mod jobs;
mod middleware;
mod routes;
mod state;

use anyhow::Result;
use axum::{middleware::from_fn, middleware::from_fn_with_state, Router};
use std::net::SocketAddr;
use tokio::net::TcpListener;
use tower_http::{
    cors::{Any, CorsLayer},
    trace::TraceLayer,
};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use state::AppState;

/// Initialize logging
///
/// Sets up tracing with:
/// - EnvFilter: Controls log levels via RUST_LOG env
/// - fmt: Pretty printing to stdout
fn init_logging() {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "termio_server=info,tower_http=debug,audit=info".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();
}

/// Build the application router
///
/// Constructs the Axum router with all routes and middleware:
/// 1. Health routes (no auth)
/// 2. API routes (with auth)
/// 3. Middleware stack (audit, sanitize, trace, CORS)
fn build_router(state: AppState) -> Router {
    // CORS configuration - allows all origins in development
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    Router::new()
        // Public health endpoints
        .merge(routes::health_routes())
        // Protected API endpoints with auth middleware
        .merge(
            routes::conversation_routes()
                .merge(routes::memory_routes())
                .merge(routes::ai_routes())
                .merge(routes::notification_routes())
                .merge(routes::sync_routes())
                .merge(routes::plugin_routes())
                .merge(routes::knowledge_graph_routes())
                .merge(routes::health_data_routes())
                .merge(routes::action_plan_routes())
                .merge(routes::subscription_routes())
                .merge(routes::payment_routes())
                .merge(routes::smart_home_routes())
                .layer(from_fn_with_state(
                    state.clone(),
                    middleware::auth::auth_middleware,
                )),
        )
        // Global middleware (order matters - applied in reverse)
        .layer(from_fn(middleware::audit::audit_middleware))  // Audit logging
        .layer(from_fn(middleware::sanitize::sanitize_middleware)) // Input sanitization
        .layer(TraceLayer::new_for_http())  // Request tracing
        .layer(cors)  // CORS headers
        .with_state(state)
}

/// Main entry point
///
/// Async runtime entry point using Tokio:
/// 1. Initialize logging
/// 2. Load configuration
/// 3. Create application state
/// 4. Start background jobs
/// 5. Build and start HTTP server
/// 6. Wait for shutdown
#[tokio::main]
async fn main() -> Result<()> {
    // Step 1: Set up logging
    init_logging();
    tracing::info!("Starting TERMIO Server...");

    // Step 2: Load configuration from files and environment
    let config = termio_core::Config::load()?;
    tracing::info!("Loaded configuration");

    // Step 3: Create shared application state
    let state = AppState::new(config).await?;
    tracing::info!("Initialized application state");

    // Step 4: Start background job scheduler
    let scheduler = jobs::JobScheduler::new();
    scheduler.start(state.clone());

    // Step 5: Build the router
    let app = build_router(state);

    // Step 6: Start HTTP server
    let addr: SocketAddr = "127.0.0.1:8080".parse()?;
    tracing::info!("Listening on {}", addr);

    let listener = TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    // Step 7: Graceful shutdown
    scheduler.shutdown();

    Ok(())
}
