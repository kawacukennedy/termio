//! Plugin marketplace client
//!
//! Client for discovering and downloading plugins from the marketplace.

use reqwest::Client;
use serde::{Deserialize, Serialize};
use termio_core::plugins::manifest::{PluginManifest, Compatibility};
use uuid::Uuid;

/// Plugin marketplace entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketplacePlugin {
    pub id: String,
    pub name: String,
    pub version: String,
    pub description: String,
    pub author: String,
    pub downloads: u64,
    pub rating: f64,
    pub categories: Vec<String>,
    pub icon_url: Option<String>,
}

/// Plugin search results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResults {
    pub plugins: Vec<MarketplacePlugin>,
    pub total: usize,
    pub page: usize,
    pub per_page: usize,
}

/// Marketplace client error
#[derive(Debug)]
pub struct MarketplaceError {
    pub message: String,
    pub status_code: Option<u16>,
}

impl std::fmt::Display for MarketplaceError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "MarketplaceError: {}", self.message)
    }
}

impl std::error::Error for MarketplaceError {}

/// Client for the plugin marketplace
pub struct MarketplaceClient {
    client: Client,
    base_url: String,
}

impl MarketplaceClient {
    /// Create a new marketplace client
    pub fn new(base_url: Option<String>) -> Self {
        Self {
            client: Client::new(),
            base_url: base_url.unwrap_or_else(|| {
                std::env::var("TERMIO_MARKETPLACE_URL")
                    .unwrap_or_else(|_| "https://marketplace.termio.com/v1".to_string())
            }),
        }
    }

    /// Search for plugins
    pub async fn search(
        &self,
        query: Option<&str>,
        category: Option<&str>,
        page: usize,
        per_page: usize,
    ) -> Result<SearchResults, MarketplaceError> {
        let mut url = format!("{}/plugins", self.base_url);
        
        let mut params = Vec::new();
        if let Some(q) = query {
            params.push(format!("q={}", urlencoding::encode(q)));
        }
        if let Some(cat) = category {
            params.push(format!("category={}", urlencoding::encode(cat)));
        }
        params.push(format!("page={}", page));
        params.push(format!("per_page={}", per_page));
        
        if !params.is_empty() {
            url = format!("{}?{}", url, params.join("&"));
        }

        let response = self.client
            .get(&url)
            .timeout(std::time::Duration::from_secs(10))
            .send()
            .await
            .map_err(|e| MarketplaceError {
                message: format!("Request failed: {}", e),
                status_code: None,
            })?;

        if !response.status().is_success() {
            return Err(MarketplaceError {
                message: format!("Marketplace returned status: {}", response.status()),
                status_code: Some(response.status().as_u16()),
            });
        }

        response
            .json::<SearchResults>()
            .await
            .map_err(|e| MarketplaceError {
                message: format!("Failed to parse response: {}", e),
                status_code: None,
            })
    }

    /// Get a specific plugin by ID
    pub async fn get_plugin(&self, plugin_id: &str) -> Result<MarketplacePlugin, MarketplaceError> {
        let url = format!("{}/plugins/{}", self.base_url, plugin_id);

        let response = self.client
            .get(&url)
            .timeout(std::time::Duration::from_secs(10))
            .send()
            .await
            .map_err(|e| MarketplaceError {
                message: format!("Request failed: {}", e),
                status_code: None,
            })?;

        if !response.status().is_success() {
            return Err(MarketplaceError {
                message: format!("Plugin not found: {}", response.status()),
                status_code: Some(response.status().as_u16()),
            });
        }

        response
            .json::<MarketplacePlugin>()
            .await
            .map_err(|e| MarketplaceError {
                message: format!("Failed to parse response: {}", e),
                status_code: None,
            })
    }

    /// Download a plugin package
    pub async fn download(&self, plugin_id: &str) -> Result<Vec<u8>, MarketplaceError> {
        let url = format!("{}/plugins/{}/download", self.base_url, plugin_id);

        let response = self.client
            .get(&url)
            .timeout(std::time::Duration::from_secs(60))
            .send()
            .await
            .map_err(|e| MarketplaceError {
                message: format!("Download failed: {}", e),
                status_code: None,
            })?;

        if !response.status().is_success() {
            return Err(MarketplaceError {
                message: format!("Download failed with status: {}", response.status()),
                status_code: Some(response.status().as_u16()),
            });
        }

        response
            .bytes()
            .await
            .map(|b| b.to_vec())
            .map_err(|e| MarketplaceError {
                message: format!("Failed to read download: {}", e),
                status_code: None,
            })
    }

    /// Verify a plugin manifest against the marketplace
    pub async fn verify(&self, manifest: &PluginManifest) -> Result<bool, MarketplaceError> {
        let url = format!("{}/plugins/verify", self.base_url);

        let response = self.client
            .post(&url)
            .json(manifest)
            .timeout(std::time::Duration::from_secs(10))
            .send()
            .await
            .map_err(|e| MarketplaceError {
                message: format!("Verification request failed: {}", e),
                status_code: None,
            })?;

        if !response.status().is_success() {
            return Ok(false);
        }

        #[derive(Deserialize)]
        struct VerifyResponse {
            valid: bool,
        }

        let result: VerifyResponse = response
            .json()
            .await
            .map_err(|e| MarketplaceError {
                message: format!("Failed to parse verification: {}", e),
                status_code: None,
            })?;

        Ok(result.valid)
    }

    /// Get available categories
    pub async fn categories(&self) -> Result<Vec<String>, MarketplaceError> {
        let url = format!("{}/categories", self.base_url);

        let response = self.client
            .get(&url)
            .timeout(std::time::Duration::from_secs(10))
            .send()
            .await
            .map_err(|e| MarketplaceError {
                message: format!("Request failed: {}", e),
                status_code: None,
            })?;

        if !response.status().is_success() {
            return Err(MarketplaceError {
                message: format!("Failed to get categories: {}", response.status()),
                status_code: Some(response.status().as_u16()),
            });
        }

        response
            .json::<Vec<String>>()
            .await
            .map_err(|e| MarketplaceError {
                message: format!("Failed to parse categories: {}", e),
                status_code: None,
            })
    }
}

impl Default for MarketplaceClient {
    fn default() -> Self {
        Self::new(None)
    }
}
