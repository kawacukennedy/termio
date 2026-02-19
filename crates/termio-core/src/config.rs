//! Configuration management for TERMIO
//!
//! Implements hierarchical configuration loading:
//! 1. Default values in code
//! 2. Environment-specific overrides (config/*.toml)
//! 3. Environment variables (TERMIO_*)

use config::{ConfigBuilder, Environment, File};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

use crate::error::Result;

/// Main application configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// Application metadata
    pub app: AppConfig,

    /// AI inference settings
    pub ai: AiConfig,

    /// Memory system settings
    pub memory: MemoryConfig,

    /// Server settings
    pub server: ServerConfig,

    /// UI settings
    pub ui: UiConfig,
}

/// Application metadata configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    /// Application name
    pub name: String,

    /// Version string
    pub version: String,

    /// Data directory path
    pub data_dir: PathBuf,

    /// Log level (trace, debug, info, warn, error)
    pub log_level: String,
}

/// AI inference configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AiConfig {
    /// Path to the AI model file
    pub model_path: Option<PathBuf>,

    /// Maximum context window size in tokens
    pub max_context_tokens: usize,

    /// Inference timeout in milliseconds
    pub inference_timeout_ms: u64,

    /// AI service URL (for Python inference service)
    pub service_url: String,

    /// Whether to use local inference
    pub local_inference: bool,
}

/// Memory system configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryConfig {
    /// Ring buffer size (last N interactions)
    pub ring_buffer_size: usize,

    /// Path to SQLite database
    pub database_path: PathBuf,

    /// Memory query timeout in milliseconds
    pub query_timeout_ms: u64,

    /// Enable vector embeddings for semantic search
    pub enable_embeddings: bool,
}

/// Server configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    /// Host to bind to
    pub host: String,

    /// Port to listen on
    pub port: u16,

    /// Enable CORS
    pub enable_cors: bool,
}

/// UI configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UiConfig {
    /// Theme (dark, light, system)
    pub theme: String,

    /// Enable animations
    pub animations: bool,

    /// Keyboard shortcut prefix
    pub shortcut_prefix: String,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            app: AppConfig {
                name: "TERMIO".to_string(),
                version: env!("CARGO_PKG_VERSION").to_string(),
                data_dir: dirs::data_dir()
                    .unwrap_or_else(|| PathBuf::from("."))
                    .join("termio"),
                log_level: "info".to_string(),
            },
            ai: AiConfig {
                model_path: None,
                max_context_tokens: 128000,
                inference_timeout_ms: 30000,
                service_url: "http://localhost:8000".to_string(),
                local_inference: true,
            },
            memory: MemoryConfig {
                ring_buffer_size: 100,
                database_path: PathBuf::from("termio.db"),
                query_timeout_ms: 50,
                enable_embeddings: false,
            },
            server: ServerConfig {
                host: "127.0.0.1".to_string(),
                port: 8080,
                enable_cors: true,
            },
            ui: UiConfig {
                theme: "dark".to_string(),
                animations: true,
                shortcut_prefix: "Ctrl".to_string(),
            },
        }
    }
}

impl Config {
    /// Load configuration from files and environment
    pub fn load() -> Result<Self> {
        Self::load_from_path(None)
    }

    /// Load configuration with a custom config directory
    pub fn load_from_path(config_dir: Option<PathBuf>) -> Result<Self> {
        let default_config = Config::default();

        let builder = ConfigBuilder::<config::builder::DefaultState>::default()
            // Start with defaults
            .set_default("app.name", default_config.app.name)?
            .set_default("app.version", default_config.app.version)?
            .set_default(
                "app.data_dir",
                default_config.app.data_dir.to_string_lossy().to_string(),
            )?
            .set_default("app.log_level", default_config.app.log_level)?
            .set_default("ai.max_context_tokens", default_config.ai.max_context_tokens as i64)?
            .set_default("ai.inference_timeout_ms", default_config.ai.inference_timeout_ms as i64)?
            .set_default("ai.service_url", default_config.ai.service_url)?
            .set_default("ai.local_inference", default_config.ai.local_inference)?
            .set_default("memory.ring_buffer_size", default_config.memory.ring_buffer_size as i64)?
            .set_default(
                "memory.database_path",
                default_config.memory.database_path.to_string_lossy().to_string(),
            )?
            .set_default("memory.query_timeout_ms", default_config.memory.query_timeout_ms as i64)?
            .set_default("memory.enable_embeddings", default_config.memory.enable_embeddings)?
            .set_default("server.host", default_config.server.host)?
            .set_default("server.port", default_config.server.port as i64)?
            .set_default("server.enable_cors", default_config.server.enable_cors)?
            .set_default("ui.theme", default_config.ui.theme)?
            .set_default("ui.animations", default_config.ui.animations)?
            .set_default("ui.shortcut_prefix", default_config.ui.shortcut_prefix)?;

        // Add config file if exists
        let builder = if let Some(dir) = config_dir {
            let config_file = dir.join("default.toml");
            if config_file.exists() {
                builder.add_source(File::from(config_file))
            } else {
                builder
            }
        } else {
            // Try default locations
            let config_file = PathBuf::from("config/default.toml");
            if config_file.exists() {
                builder.add_source(File::from(config_file))
            } else {
                builder
            }
        };

        // Add environment variables with TERMIO_ prefix
        let builder = builder.add_source(
            Environment::with_prefix("TERMIO")
                .separator("_")
                .try_parsing(true),
        );

        let settings = builder.build()?;
        let config: Config = settings.try_deserialize()?;

        Ok(config)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert_eq!(config.app.name, "TERMIO");
        assert_eq!(config.memory.ring_buffer_size, 100);
        assert_eq!(config.server.port, 8080);
    }
}
