//! Request handlers

use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use hedtronix_core::models::{Conversation, MemoryEntry, Message};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::state::AppState;

// ============================================================================
// Health
// ============================================================================

/// Health check response
#[derive(Serialize)]
pub struct HealthResponse {
    status: String,
    version: String,
}

/// Health check handler
pub async fn health_check() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
    })
}

// ============================================================================
// Conversations
// ============================================================================

/// List conversations response
#[derive(Serialize)]
pub struct ConversationsResponse {
    conversations: Vec<ConversationSummary>,
}

/// Conversation summary for list view
#[derive(Serialize)]
pub struct ConversationSummary {
    id: String,
    message_count: usize,
    created_at: String,
    updated_at: String,
}

/// List all conversations
pub async fn list_conversations(
    State(_state): State<AppState>,
) -> Json<ConversationsResponse> {
    // TODO: Implement actual listing from database
    Json(ConversationsResponse {
        conversations: Vec::new(),
    })
}

/// Create conversation request
#[derive(Deserialize)]
pub struct CreateConversationRequest {
    initial_message: Option<String>,
}

/// Create a new conversation
pub async fn create_conversation(
    State(state): State<AppState>,
    Json(req): Json<CreateConversationRequest>,
) -> Result<Json<Conversation>, StatusCode> {
    let user_id = Uuid::new_v4(); // TODO: Get from auth
    let device_id = Uuid::new_v4(); // TODO: Get from headers

    let mut conversation = Conversation::new(user_id, device_id);

    if let Some(message) = req.initial_message {
        conversation.add_message(Message::user(message));
    }

    // Save to database
    {
        let store = state.memory_store.read().await;
        store
            .save_conversation(&conversation)
            .await
            .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    }

    Ok(Json(conversation))
}

/// Get a conversation by ID
pub async fn get_conversation(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<Json<Conversation>, StatusCode> {
    let store = state.memory_store.read().await;
    match store.get_conversation(&id).await {
        Ok(Some(conv)) => Ok(Json(conv)),
        Ok(None) => Err(StatusCode::NOT_FOUND),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

/// Add message request
#[derive(Deserialize)]
pub struct AddMessageRequest {
    content: String,
    role: Option<String>,
}

/// Add a message to a conversation
pub async fn add_message(
    State(state): State<AppState>,
    Path(id): Path<String>,
    Json(req): Json<AddMessageRequest>,
) -> Result<Json<Message>, StatusCode> {
    let store = state.memory_store.read().await;

    // Get existing conversation
    let mut conversation = store
        .get_conversation(&id)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .ok_or(StatusCode::NOT_FOUND)?;

    // Create message
    let message = Message::user(req.content);
    conversation.add_message(message.clone());

    // Save updated conversation
    store
        .save_conversation(&conversation)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(message))
}

// ============================================================================
// Memory
// ============================================================================

/// Search memory query
#[derive(Deserialize)]
pub struct SearchMemoryQuery {
    q: String,
    limit: Option<i32>,
}

/// Search memory response
#[derive(Serialize)]
pub struct SearchMemoryResponse {
    entries: Vec<MemoryEntry>,
    count: usize,
}

/// Search memory entries
pub async fn search_memory(
    State(state): State<AppState>,
    Query(query): Query<SearchMemoryQuery>,
) -> Result<Json<SearchMemoryResponse>, StatusCode> {
    let user_id = Uuid::new_v4().to_string(); // TODO: Get from auth
    let limit = query.limit.unwrap_or(10);

    let store = state.memory_store.read().await;
    let entries = store
        .search_memory(&user_id, &query.q, limit)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let count = entries.len();
    Ok(Json(SearchMemoryResponse { entries, count }))
}

/// Create memory entry request
#[derive(Deserialize)]
pub struct CreateMemoryRequest {
    content: String,
    tags: Option<Vec<String>>,
}

/// Create a new memory entry
pub async fn create_memory_entry(
    State(state): State<AppState>,
    Json(req): Json<CreateMemoryRequest>,
) -> Result<Json<MemoryEntry>, StatusCode> {
    let user_id = Uuid::new_v4(); // TODO: Get from auth

    let mut entry = MemoryEntry::new(user_id, req.content);
    if let Some(tags) = req.tags {
        entry = entry.with_tags(tags);
    }

    let store = state.memory_store.read().await;
    store
        .save_memory_entry(&entry)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(entry))
}

// ============================================================================
// AI
// ============================================================================

/// Chat request
#[derive(Deserialize)]
pub struct ChatRequest {
    message: String,
    conversation_id: Option<String>,
}

/// Chat response
#[derive(Serialize)]
pub struct ChatResponse {
    response: String,
    conversation_id: String,
    model_used: String,
    processing_time_ms: u64,
}

/// Chat with AI
pub async fn chat(
    State(state): State<AppState>,
    Json(req): Json<ChatRequest>,
) -> Result<Json<ChatResponse>, StatusCode> {
    let start = std::time::Instant::now();

    // Try to call the AI service
    let client = reqwest::Client::new();
    let ai_response = client
        .post(format!("{}/chat", state.ai_service_url))
        .json(&serde_json::json!({
            "message": req.message,
            "max_tokens": 512
        }))
        .send()
        .await;

    let response_text = match ai_response {
        Ok(resp) if resp.status().is_success() => {
            let body: serde_json::Value = resp.json().await.unwrap_or_default();
            body["response"].as_str().unwrap_or("").to_string()
        }
        _ => {
            // Fallback response if AI service is unavailable
            format!(
                "I received your message: \"{}\"\n\n\
                The AI inference service is not available. \
                Please start the AI service to enable responses.",
                req.message
            )
        }
    };

    let processing_time_ms = start.elapsed().as_millis() as u64;

    Ok(Json(ChatResponse {
        response: response_text,
        conversation_id: req.conversation_id.unwrap_or_else(|| Uuid::new_v4().to_string()),
        model_used: "llama-7b".to_string(),
        processing_time_ms,
    }))
}

/// AI status response
#[derive(Serialize)]
pub struct AiStatusResponse {
    available: bool,
    model_loaded: bool,
    service_url: String,
}

/// Get AI service status
pub async fn ai_status(State(state): State<AppState>) -> Json<AiStatusResponse> {
    // Try to ping the AI service
    let client = reqwest::Client::new();
    let available = client
        .get(format!("{}/health", state.ai_service_url))
        .timeout(std::time::Duration::from_secs(2))
        .send()
        .await
        .is_ok();

    Json(AiStatusResponse {
        available,
        model_loaded: false, // Would need to query the service
        service_url: state.ai_service_url.clone(),
    })
}
