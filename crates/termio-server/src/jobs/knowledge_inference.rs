//! Knowledge inference background job
//!
//! Traverses recent memory entries, extracts entities and relationships,
//! and enriches the knowledge graph with inferred connections.
//! Spec: runs daily at 4 AM.

use crate::state::AppState;

/// Run knowledge graph inference
pub async fn run(state: &AppState) {
    tracing::info!("Starting knowledge inference job...");

    // Step 1: Fetch recent memory entries for analysis
    let entries = fetch_recent_entries(state).await;
    if entries.is_empty() {
        tracing::debug!("No recent entries for inference, skipping");
        return;
    }

    tracing::info!("Analyzing {} entries for knowledge extraction", entries.len());

    // Step 2: Call AI service to extract entities and relationships
    if let Err(e) = extract_and_link(state, &entries).await {
        tracing::error!("Knowledge extraction failed: {}", e);
        return;
    }

    // Step 3: Prune low-importance edges that haven't been reinforced
    let pruned = prune_weak_edges(state).await;
    if pruned > 0 {
        tracing::info!("Pruned {} weak knowledge edges", pruned);
    }

    tracing::info!("Knowledge inference job completed");
}

/// Fetch memory entries created in the last 24 hours
async fn fetch_recent_entries(state: &AppState) -> Vec<serde_json::Value> {
    let store = state.memory_store.read().await;
    store.get_recent_entries(100).await.unwrap_or_default()
}

/// Use AI service NLU to extract entities and link them into the knowledge graph
async fn extract_and_link(
    state: &AppState,
    entries: &[serde_json::Value],
) -> Result<(), String> {
    let ai_url = &state.ai_service_url;
    let client = reqwest::Client::new();

    for entry in entries {
        let text = entry
            .get("content")
            .and_then(|v| v.as_str())
            .unwrap_or_default();

        if text.is_empty() {
            continue;
        }

        // Call the NLU endpoint for entity extraction
        let resp = client
            .post(format!("{}/nlu", ai_url))
            .json(&serde_json::json!({ "text": text }))
            .timeout(std::time::Duration::from_secs(30))
            .send()
            .await
            .map_err(|e| format!("NLU request failed: {}", e))?;

        if !resp.status().is_success() {
            continue;
        }

        let nlu_result: serde_json::Value = resp
            .json()
            .await
            .map_err(|e| format!("Failed to parse NLU response: {}", e))?;

        // Extract entities and create knowledge nodes
        if let Some(entities) = nlu_result.get("entities").and_then(|v| v.as_array()) {
            let store = state.memory_store.read().await;
            for entity in entities {
                let name = entity
                    .get("text")
                    .and_then(|v| v.as_str())
                    .unwrap_or_default();
                let entity_type = entity
                    .get("type")
                    .and_then(|v| v.as_str())
                    .unwrap_or("concept");

                if !name.is_empty() {
                    let id = uuid::Uuid::new_v4().to_string();
                    let props = serde_json::json!({ "importance": 1.0 });
                    let _ = store
                        .save_knowledge_node(&id, "system", entity_type, name, &props)
                        .await;
                }
            }
        }
    }

    Ok(())
}

/// Remove knowledge graph edges with importance below threshold
async fn prune_weak_edges(state: &AppState) -> usize {
    let store = state.memory_store.read().await;
    store.prune_knowledge_edges(0.1).await.unwrap_or(0) as usize
}
