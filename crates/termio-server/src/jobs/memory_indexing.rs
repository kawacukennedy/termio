//! Memory indexing background job
//!
//! Maintains vector index for semantic search.
//! Spec: runs every 6 hours, 512MB max, 300s max duration.

use crate::state::AppState;

/// Run memory indexing maintenance
pub async fn run(state: &AppState) {
    tracing::info!("Starting memory indexing job...");

    // Step 1: Check for unindexed memory entries
    let unindexed_count = check_unindexed(state).await;
    if unindexed_count == 0 {
        tracing::debug!("No unindexed entries found, skipping");
        return;
    }

    tracing::info!("Found {} unindexed memory entries", unindexed_count);

    // Step 2: Generate embeddings for new entries
    if let Err(e) = generate_embeddings(state, unindexed_count).await {
        tracing::error!("Failed to generate embeddings: {}", e);
        return;
    }

    // Step 3: Clean up stale entries (older than 30 days with no access)
    let cleaned = cleanup_stale(state).await;
    if cleaned > 0 {
        tracing::info!("Cleaned up {} stale memory entries", cleaned);
    }

    tracing::info!("Memory indexing job completed");
}

/// Check for memory entries without embeddings
async fn check_unindexed(state: &AppState) -> usize {
    let store = state.memory_store.read().await;
    store.count_unindexed_entries().await.unwrap_or(0) as usize
}

/// Generate embeddings for unindexed entries via the AI service
async fn generate_embeddings(state: &AppState, _count: usize) -> Result<(), String> {
    let ai_url = &state.ai_service_url;
    let store = state.memory_store.read().await;

    // Fetch entries that have no embedding yet (limit batch to 50)
    let entries = store
        .get_unindexed_entries(50)
        .await
        .map_err(|e| format!("Failed to fetch unindexed entries: {}", e))?;

    if entries.is_empty() {
        return Ok(());
    }

    // Build texts for embedding generation
    let texts: Vec<String> = entries
        .iter()
        .map(|e| e.content.clone())
        .collect();

    // Call the AI service /embeddings endpoint
    let client = reqwest::Client::new();
    let resp = client
        .post(format!("{}/embeddings", ai_url))
        .json(&serde_json::json!({ "texts": texts }))
        .timeout(std::time::Duration::from_secs(120))
        .send()
        .await
        .map_err(|e| format!("AI service unreachable: {}", e))?;

    if !resp.status().is_success() {
        return Err(format!("AI service returned {}", resp.status()));
    }

    let body: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| format!("Failed to parse embeddings response: {}", e))?;

    // Store embeddings back into each entry
    if let Some(embeddings) = body.get("embeddings").and_then(|v| v.as_array()) {
        for (i, entry) in entries.iter().enumerate() {
            if let Some(emb) = embeddings.get(i) {
                let emb_str = serde_json::to_string(emb).unwrap_or_default();
                let _ = store.update_embedding(&entry.id.to_string(), &emb_str).await;
            }
        }
    }

    Ok(())
}

/// Remove stale entries older than retention period with zero access
async fn cleanup_stale(state: &AppState) -> usize {
    let store = state.memory_store.read().await;
    store.cleanup_stale_entries(30).await.unwrap_or(0) as usize
}
