//! HEDTRONIX Backend Server
//!
//! Provides HTTP API for the AI assistant.

mod handlers;
mod middleware;
mod routes;
mod state;

use anyhow::Result;
use axum::{middleware::from_fn_with_state, Router};
use std::net::SocketAddr;
use tokio::net::TcpListener;
use tower_http::{
    cors::{Any, CorsLayer},
    trace::TraceLayer,
};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use state::AppState;

/// Initialize logging
fn init_logging() {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "hedtronix_server=info,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();
}

/// Build the application router
fn build_router(state: AppState) -> Router {
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    Router::new()
        .merge(routes::health_routes())
        .merge(
            routes::conversation_routes()
                .merge(routes::memory_routes())
                .merge(routes::ai_routes())
                .layer(from_fn_with_state(
                    state.clone(),
                    middleware::auth::auth_middleware,
                )),
        )
        .layer(TraceLayer::new_for_http())
        .layer(cors)
        .with_state(state)
}

/// Main entry point
#[tokio::main]
async fn main() -> Result<()> {
    init_logging();
    tracing::info!("Starting HEDTRONIX Server...");

    // Load configuration
    let config = hedtronix_core::Config::load()?;
    tracing::info!("Loaded configuration");

    // Create application state
    let state = AppState::new(config).await?;
    tracing::info!("Initialized application state");

    // Build router
    let app = build_router(state);

    // Start server
    let addr: SocketAddr = "127.0.0.1:8080".parse()?;
    tracing::info!("Listening on {}", addr);

    let listener = TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
