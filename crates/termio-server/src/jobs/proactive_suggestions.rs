//! Proactive suggestion generation job
//!
//! Runs periodically to analyze recent context and generate helpful suggestions
//! for the user (e.g., "You have a meeting soon", "Remember to reply to X").

use crate::state::AppState;
use serde_json::json;
use std::time::Duration;

/// Run the proactive suggestion generation job
pub async fn run(state: &AppState) {
    tracing::info!("Starting proactive suggestion generation...");

    // 1. Get recent memory entries (last 24 hours) as context
    let store = state.memory_store.read().await;
    let recent_entries = match store.search_memory("__health_check__", "", 50).await {
        Ok(entries) => entries,
        Err(e) => {
            tracing::error!("Failed to fetch recent entries for suggestions: {}", e);
            return;
        }
    };
    drop(store);

    if recent_entries.is_empty() {
        tracing::debug!("No recent entries to analyze for suggestions");
        return;
    }

    // 2. Format context for AI
    let context_str = serde_json::to_string(&recent_entries).unwrap_or_default();
    
    // 3. Ask AI for suggestions (using chat endpoint)
    // We use a system prompt that asks for JSON output
    let system_prompt = r#"
    You are an intelligent assistant analyzing user activity to provide proactive suggestions.
    Based on the recent memory entries provided, suggest up to 3 helpful actions or reminders.
    
    Output purely a JSON array of strings, e.g.:
    ["Check the weather for your trip tomorrow", "Reply to John's email"]
    
    If no obvious suggestions are needed, return an empty array [].
    Do not output markdown formatting, just raw JSON.
    "#;

    let request = json!({
        "message": format!("{} Recent activity context: {}", system_prompt, context_str),
        "temperature": 0.7
    });

    let client = reqwest::Client::new();
    let ai_url = format!("{}/chat", state.config.ai.service_url);

    match client.post(&ai_url)
        .json(&request)
        .timeout(Duration::from_secs(30))
        .send()
        .await 
    {
        Ok(res) => {
            if let Ok(response_json) = res.json::<serde_json::Value>().await {
                if let Some(response_text) = response_json.get("response").and_then(|c| c.as_str()) {
                    // 4. Parse suggestions
                    if let Ok(suggestions) = serde_json::from_str::<Vec<String>>(response_text) {
                        for suggestion in suggestions {
                            // 5. Create notification for each suggestion
                            let notification = termio_core::notifications::Notification::system(
                                "Proactive Suggestion",
                                &suggestion,
                            )
                            .with_type(termio_core::notifications::NotificationType::Suggestion);
                            state.notification_manager.notify(notification);
                            tracing::info!("Generated suggestion: {}", suggestion);
                        }
                    } else {
                         // Fallback if AI didn't return valid JSON, maybe it returned text
                         tracing::debug!("AI response was not valid JSON array: {}", response_text);
                    }
                }
            }
        }
        Err(e) => {
            tracing::warn!("Failed to query AI for suggestions: {}", e);
        }
    }

    tracing::info!("Proactive suggestion generation completed");
}
