//! Application state

use anyhow::Result;
use termio_core::{
    auth::SessionManager,
    events::EventBus,
    health::HealthMonitor,
    memory::MemoryStore,
    notifications::NotificationManager,
    Config,
};
use std::sync::Arc;
use tokio::sync::RwLock;

/// Shared application state
#[derive(Clone)]
pub struct AppState {
    /// Application configuration
    pub config: Arc<Config>,

    /// Memory store
    pub memory_store: Arc<RwLock<MemoryStore>>,

    /// AI service URL
    pub ai_service_url: String,

    /// Session manager for JWT auth
    pub session_manager: Arc<SessionManager>,

    /// Event bus for system-wide communication
    pub event_bus: EventBus,

    /// Notification manager
    pub notification_manager: NotificationManager,

    /// Health monitor
    pub health_monitor: Arc<HealthMonitor>,
}

impl AppState {
    /// Create new application state
    pub async fn new(config: Config) -> Result<Self> {
        // Initialize memory store
        let db_path = &config.memory.database_path;
        let memory_store = MemoryStore::new(db_path).await?;

        // Initialize session manager with a default secret
        // In production, this would come from secure config/env
        let session_secret = std::env::var("TERMIO_SESSION_SECRET")
            .unwrap_or_else(|_| "default-dev-secret-change-in-production".to_string());
        let session_manager = SessionManager::new(session_secret.as_bytes());

        let ai_service_url = config.ai.service_url.clone();

        Ok(Self {
            ai_service_url: ai_service_url.clone(),
            config: Arc::new(config),
            memory_store: Arc::new(RwLock::new(memory_store)),
            session_manager: Arc::new(session_manager),
            event_bus: EventBus::default(),
            notification_manager: NotificationManager::default(),
            health_monitor: Arc::new(HealthMonitor::new(ai_service_url)),
        })
    }
}
