//! Configuration management for TERMIO
//!
//! This module implements hierarchical configuration loading with the following priority:
//! 1. Default values embedded in code
//! 2. Environment-specific overrides from config/*.toml files
//! 3. Environment variables (TERMIO_*) for runtime overrides
//!
//! # Configuration Hierarchy
//!
//! ```text
//! Highest Priority:  Environment variables (TERMIO_SERVER_PORT=9000)
//!                    ↓
//! Middle Priority:   Config file (config/default.toml)
//!                    ↓
//! Lowest Priority:   Code defaults (Config::default())
//! ```
//!
//! # Configuration Sections
//!
//! - **app**: Application metadata (name, version, data directory, log level)
//! - **ai**: AI inference settings (model path, context tokens, timeout, service URL)
//! - **memory**: Memory system settings (ring buffer size, database path, query timeout)
//! - **server**: HTTP server settings (host, port, CORS)
//! - **ui**: User interface settings (theme, animations, keyboard shortcuts)
//!
//! # Usage
//!
//! ```rust
//! use termio_core::Config;
//!
//! // Load configuration with defaults and overrides
//! let config = Config::load()?;
//!
//! // Or specify a custom config directory
//! let config = Config::load_from_path(Some("/etc/termio".into()))?;
//! ```

use config::{ConfigBuilder, Environment, File};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// Main application configuration
///
/// This is the root configuration struct that contains all settings
/// for the TERMIO application. It is deserialized from config files
/// and environment variables.
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
///
/// Contains basic application information and paths.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    /// Application name (default: "TERMIO")
    pub name: String,

    /// Version string (from Cargo.toml)
    pub version: String,

    /// Data directory path for storing application data
    /// Defaults to ~/.local/share/termio on Unix systems
    pub data_dir: PathBuf,

    /// Log level (trace, debug, info, warn, error)
    /// Default: "info"
    pub log_level: String,
}

/// AI inference configuration
///
/// Controls local and cloud AI behavior.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AiConfig {
    /// Path to the AI model file (e.g., LLaMA weights)
    /// If None, uses bundled or remote model
    pub model_path: Option<PathBuf>,

    /// Maximum context window size in tokens
    /// Default: 128000 (LLaMA 3 context size)
    pub max_context_tokens: usize,

    /// Inference timeout in milliseconds
    /// Default: 30000ms (30 seconds)
    pub inference_timeout_ms: u64,

    /// AI service URL for cloud augmentation
    /// Default: "http://localhost:8000"
    pub service_url: String,

    /// Whether to use local inference
    /// When true, runs AI locally; when false, uses cloud only
    /// Default: true (offline-first)
    pub local_inference: bool,
}

/// Memory system configuration
///
/// Controls the three-tier memory architecture.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryConfig {
    /// Ring buffer size (number of recent interactions to keep in memory)
    /// Per spec: 100 interactions
    pub ring_buffer_size: usize,

    /// Path to SQLite database for persistent storage
    pub database_path: PathBuf,

    /// Memory query timeout in milliseconds
    /// Used for vector search and knowledge graph queries
    pub query_timeout_ms: u64,

    /// Enable vector embeddings for semantic search
    /// When false, only exact text matching is available
    pub enable_embeddings: bool,
}

/// Server configuration
///
/// HTTP server settings for the API.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    /// Host to bind to (e.g., "127.0.0.1" or "0.0.0.0")
    pub host: String,

    /// Port to listen on
    pub port: u16,

    /// Enable CORS (Cross-Origin Resource Sharing)
    /// Should be false in production with proper reverse proxy
    pub enable_cors: bool,
}

/// UI configuration
///
/// Terminal and desktop UI settings.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UiConfig {
    /// Theme (dark, light, system)
    /// "system" follows OS preference
    pub theme: String,

    /// Enable animations
    /// Can be disabled for performance on slow terminals
    pub animations: bool,

    /// Keyboard shortcut prefix
    /// "Ctrl" on most systems, "Cmd" on macOS
    pub shortcut_prefix: String,
}

impl Default for Config {
    /// Creates default configuration with sensible production-ready values
    fn default() -> Self {
        Self {
            // Application defaults
            app: AppConfig {
                name: "TERMIO".to_string(),
                version: env!("CARGO_PKG_VERSION").to_string(),
                data_dir: dirs::data_dir()
                    .unwrap_or_else(|| PathBuf::from("."))
                    .join("termio"),
                log_level: "info".to_string(),
            },
            // AI defaults - optimized for local inference
            ai: AiConfig {
                model_path: None,
                max_context_tokens: 128000,
                inference_timeout_ms: 30000,
                service_url: "http://localhost:8000".to_string(),
                local_inference: true,
            },
            // Memory defaults - per spec requirements
            memory: MemoryConfig {
                ring_buffer_size: 100,
                database_path: PathBuf::from("termio.db"),
                query_timeout_ms: 50,
                enable_embeddings: false,
            },
            // Server defaults - local development
            server: ServerConfig {
                host: "127.0.0.1".to_string(),
                port: 8080,
                enable_cors: true,
            },
            // UI defaults
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
    ///
    /// This is the main entry point for configuration loading.
    /// It merges defaults, config file, and environment variables.
    ///
    /// # Precedence (highest to lowest)
    /// 1. Environment variables (TERMIO_*)
    /// 2. Config file (config/default.toml)
    /// 3. Code defaults
    ///
    /// # Returns
    ///
    /// Returns a `Result<Config>` with the merged configuration,
    /// or an error if configuration loading fails.
    ///
    /// # Example
    ///
    /// ```rust
    /// let config = Config::load().expect("Failed to load config");
    /// println!("Server running on {}:{}", config.server.host, config.server.port);
    /// ```
    pub fn load() -> Result<Self> {
        Self::load_from_path(None)
    }

    /// Load configuration with a custom config directory
    ///
    /// Allows specifying an alternate location for config files.
    /// If the directory or config file doesn't exist, uses defaults.
    ///
    /// # Arguments
    ///
    /// * `config_dir` - Optional path to config directory containing default.toml
    ///
    /// # Returns
    ///
    /// Returns a `Result<Config>` with the merged configuration.
    pub fn load_from_path(config_dir: Option<PathBuf>) -> Result<Self> {
        // Start with hardcoded defaults
        let default_config = Config::default();

        // Build configuration incrementally, layer by layer
        let builder = ConfigBuilder::<config::builder::DefaultState>::default()
            // Layer 1: Code defaults (lowest priority)
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

        // Layer 2: Config file (medium priority)
        let builder = if let Some(dir) = config_dir {
            // Use provided config directory
            let config_file = dir.join("default.toml");
            if config_file.exists() {
                builder.add_source(File::from(config_file))
            } else {
                builder
            }
        } else {
            // Try default locations: config/default.toml
            let config_file = PathBuf::from("config/default.toml");
            if config_file.exists() {
                builder.add_source(File::from(config_file))
            } else {
                builder
            }
        };

        // Layer 3: Environment variables (highest priority)
        // TERMIO_SERVER_PORT=9000 would override server.port
        let builder = builder.add_source(
            Environment::with_prefix("TERMIO")
                .separator("_")
                .try_parsing(true),
        );

        // Build and deserialize final configuration
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
