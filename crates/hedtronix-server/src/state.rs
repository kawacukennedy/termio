//! Application state

use anyhow::Result;
use hedtronix_core::{memory::MemoryStore, Config};
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
}

impl AppState {
    /// Create new application state
    pub async fn new(config: Config) -> Result<Self> {
        // Initialize memory store
        let db_path = &config.memory.database_path;
        let memory_store = MemoryStore::new(db_path).await?;

        Ok(Self {
            ai_service_url: config.ai.service_url.clone(),
            config: Arc::new(config),
            memory_store: Arc::new(RwLock::new(memory_store)),
        })
    }
}
