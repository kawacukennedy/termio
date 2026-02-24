//! Request handlers

use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    Json,
};
use termio_core::models::{Conversation, MemoryEntry, Message};
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
// System Health (detailed)
// ============================================================================

/// System health handler (detailed status)
pub async fn system_health(
    State(state): State<AppState>,
) -> Json<serde_json::Value> {
    let db_ok = {
        let store = state.memory_store.read().await;
        // Simple connectivity check — attempt a trivial query
        store.search_memory("__health_check__", "__probe__", 1).await.is_ok()
    };

    // Check AI service availability
    let client = reqwest::Client::new();
    let ai_available = client
        .get(format!("{}/health", state.ai_service_url))
        .timeout(std::time::Duration::from_secs(2))
        .send()
        .await
        .is_ok();

    let ai_service = termio_core::health::HealthMonitor::check_service(
        "ai_inference",
        ai_available,
        None,
        if ai_available { None } else { Some("AI service unreachable".into()) },
    );

    let report = state.health_monitor.report(db_ok, vec![ai_service]);
    Json(serde_json::to_value(report).unwrap_or_default())
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
    State(state): State<AppState>,
) -> Json<ConversationsResponse> {
    let store = state.memory_store.read().await;
    let convs = store
        .list_all_conversations(50)
        .await
        .unwrap_or_default();

    let conversations = convs
        .iter()
        .map(|c| ConversationSummary {
            id: c.id.to_string(),
            message_count: c.messages.len(),
            created_at: c.created_at.to_rfc3339(),
            updated_at: c.updated_at.to_rfc3339(),
        })
        .collect();

    Json(ConversationsResponse { conversations })
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
    let user_id = Uuid::new_v4(); // TODO: Extract from JWT claims via request extensions
    let device_id = Uuid::new_v4();

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
    #[allow(dead_code)]
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
    let user_id = Uuid::new_v4().to_string(); // TODO: Extract from JWT claims
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
    let user_id = Uuid::new_v4(); // TODO: Extract from JWT claims

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

    // Publish AI completion event to event bus
    state.notification_manager.notify(
        termio_core::notifications::Notification::ai(
            "AI Response",
            &format!("Response generated in {}ms", processing_time_ms),
        ),
    );

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
    let client = reqwest::Client::new();
    let available = client
        .get(format!("{}/health", state.ai_service_url))
        .timeout(std::time::Duration::from_secs(2))
        .send()
        .await
        .is_ok();

    Json(AiStatusResponse {
        available,
        model_loaded: false,
        service_url: state.ai_service_url.clone(),
    })
}

// ============================================================================
// Notifications
// ============================================================================

/// Notification list response
#[derive(Serialize)]
pub struct NotificationsResponse {
    notifications: Vec<termio_core::notifications::Notification>,
    unread_count: usize,
}

/// List notifications
pub async fn list_notifications(
    State(state): State<AppState>,
) -> Json<NotificationsResponse> {
    let notifications = state.notification_manager.all();
    let unread_count = state.notification_manager.unread_count();
    Json(NotificationsResponse {
        notifications,
        unread_count,
    })
}

/// Dismiss a notification
pub async fn dismiss_notification(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<StatusCode, StatusCode> {
    if state.notification_manager.dismiss(id) {
        Ok(StatusCode::NO_CONTENT)
    } else {
        Err(StatusCode::NOT_FOUND)
    }
}

/// Mark notification as read
pub async fn mark_notification_read(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<StatusCode, StatusCode> {
    if state.notification_manager.mark_read(id) {
        Ok(StatusCode::NO_CONTENT)
    } else {
        Err(StatusCode::NOT_FOUND)
    }
}

// ============================================================================
// Sync
// ============================================================================

/// Sync status response
#[derive(Serialize)]
pub struct SyncStatusResponse {
    status: String,
    last_sync: Option<String>,
    pending_changes: u32,
}

/// Get sync status
pub async fn sync_status(
    State(state): State<AppState>,
) -> Json<SyncStatusResponse> {
    let store = state.memory_store.read().await;
    let pending = store.count_unindexed_entries().await.unwrap_or(0) as u32;
    Json(SyncStatusResponse {
        status: if pending > 0 { "pending".to_string() } else { "idle".to_string() },
        last_sync: Some(chrono::Utc::now().to_rfc3339()),
        pending_changes: pending,
    })
}

// ============================================================================
// Plugins
// ============================================================================

/// Plugin info response
#[derive(Serialize)]
pub struct PluginInfo {
    id: String,
    name: String,
    version: String,
    enabled: bool,
}

/// Plugin list response
#[derive(Serialize)]
pub struct PluginsResponse {
    plugins: Vec<PluginInfo>,
}

/// List installed plugins
pub async fn list_plugins(
    State(state): State<AppState>,
) -> Json<PluginsResponse> {
    let store = state.memory_store.read().await;
    let db_plugins = store.list_plugins().await.unwrap_or_default();
    let plugins = db_plugins
        .iter()
        .map(|p| PluginInfo {
            id: p["id"].as_str().unwrap_or_default().to_string(),
            name: p["name"].as_str().unwrap_or_default().to_string(),
            version: p["version"].as_str().unwrap_or_default().to_string(),
            enabled: p["enabled"].as_bool().unwrap_or(false),
        })
        .collect();
    Json(PluginsResponse { plugins })
}

/// Install plugin request
#[derive(Deserialize)]
pub struct InstallPluginRequest {
    name: String,
    version: Option<String>,
    #[allow(dead_code)]
    manifest_url: Option<String>,
}

/// Install a plugin
pub async fn install_plugin(
    State(state): State<AppState>,
    Json(req): Json<InstallPluginRequest>,
) -> Result<Json<PluginInfo>, StatusCode> {
    let id = Uuid::new_v4().to_string();
    let version = req.version.unwrap_or_else(|| "1.0.0".to_string());
    let store = state.memory_store.read().await;
    store
        .save_plugin(&id, &req.name, &version, None, true)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(PluginInfo {
        id,
        name: req.name,
        version,
        enabled: true,
    }))
}

/// Toggle plugin enabled/disabled
pub async fn toggle_plugin(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<StatusCode, StatusCode> {
    let store = state.memory_store.read().await;
    if store.toggle_plugin(&id).await.map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)? {
        Ok(StatusCode::NO_CONTENT)
    } else {
        Err(StatusCode::NOT_FOUND)
    }
}

/// Uninstall a plugin
pub async fn uninstall_plugin(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<StatusCode, StatusCode> {
    let store = state.memory_store.read().await;
    if store.delete_plugin(&id).await.map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)? {
        Ok(StatusCode::NO_CONTENT)
    } else {
        Err(StatusCode::NOT_FOUND)
    }
}

// ============================================================================
// Knowledge Graph (FA-003)
// ============================================================================

/// Knowledge node response
#[derive(Serialize, Deserialize)]
pub struct KnowledgeNodeResponse {
    id: String,
    node_type: String,
    label: String,
    properties: serde_json::Value,
}

/// Knowledge graph query
#[derive(Deserialize)]
pub struct KnowledgeQueryParams {
    q: Option<String>,
    node_type: Option<String>,
    limit: Option<i32>,
}

/// Query knowledge graph
pub async fn query_knowledge_graph(
    State(state): State<AppState>,
    Query(params): Query<KnowledgeQueryParams>,
) -> Json<serde_json::Value> {
    let user_id = Uuid::new_v4().to_string(); // TODO: Extract from JWT
    let limit = params.limit.unwrap_or(50);
    let store = state.memory_store.read().await;

    let nodes = store
        .query_knowledge_nodes(&user_id, params.q.as_deref(), params.node_type.as_deref(), limit)
        .await
        .unwrap_or_default();

    let node_ids: Vec<String> = nodes.iter()
        .filter_map(|n| n["id"].as_str().map(String::from))
        .collect();

    let edges = store
        .query_knowledge_edges(&node_ids)
        .await
        .unwrap_or_default();

    let count = nodes.len();
    Json(serde_json::json!({
        "nodes": nodes,
        "edges": edges,
        "count": count
    }))
}

/// Create knowledge node request
#[derive(Deserialize)]
pub struct CreateKnowledgeNodeRequest {
    node_type: String,
    label: String,
    properties: Option<serde_json::Value>,
}

/// Create a knowledge node
pub async fn create_knowledge_node(
    State(state): State<AppState>,
    Json(req): Json<CreateKnowledgeNodeRequest>,
) -> Result<Json<KnowledgeNodeResponse>, StatusCode> {
    let id = Uuid::new_v4().to_string();
    let user_id = Uuid::new_v4().to_string(); // TODO: Extract from JWT
    let properties = req.properties.clone().unwrap_or(serde_json::json!({}));

    let store = state.memory_store.read().await;
    store
        .save_knowledge_node(&id, &user_id, &req.node_type, &req.label, &properties)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(KnowledgeNodeResponse {
        id,
        node_type: req.node_type,
        label: req.label,
        properties,
    }))
}

/// Create knowledge edge request
#[derive(Deserialize)]
pub struct CreateKnowledgeEdgeRequest {
    source_id: String,
    target_id: String,
    relationship: String,
    weight: Option<f64>,
}

/// Create a knowledge edge
pub async fn create_knowledge_edge(
    State(state): State<AppState>,
    Json(req): Json<CreateKnowledgeEdgeRequest>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    let id = Uuid::new_v4().to_string();
    let weight = req.weight.unwrap_or(1.0);

    let store = state.memory_store.read().await;
    store
        .save_knowledge_edge(&id, &req.source_id, &req.target_id, &req.relationship, weight)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(serde_json::json!({
        "id": id,
        "source_id": req.source_id,
        "target_id": req.target_id,
        "relationship": req.relationship,
        "weight": weight
    })))
}

// ============================================================================
// Health Data (FA-008)
// ============================================================================

/// Health data query params
#[derive(Deserialize)]
pub struct HealthDataQuery {
    data_type: Option<String>,
    from: Option<String>,
    to: Option<String>,
    limit: Option<i32>,
}

/// List health data entries
pub async fn list_health_data(
    State(state): State<AppState>,
    Query(params): Query<HealthDataQuery>,
) -> Json<serde_json::Value> {
    let user_id = Uuid::new_v4().to_string(); // TODO: Extract from JWT
    let limit = params.limit.unwrap_or(50);
    let store = state.memory_store.read().await;

    let entries = store
        .list_health_data(
            &user_id,
            params.data_type.as_deref(),
            params.from.as_deref(),
            params.to.as_deref(),
            limit,
        )
        .await
        .unwrap_or_default();

    let count = entries.len();
    Json(serde_json::json!({
        "entries": entries,
        "count": count
    }))
}

/// Create health data request
#[derive(Deserialize)]
pub struct CreateHealthDataRequest {
    source: String,
    data_type: String,
    value: f64,
    unit: String,
    confidence: Option<f64>,
}

/// Create a health data entry
pub async fn create_health_data(
    State(state): State<AppState>,
    Json(req): Json<CreateHealthDataRequest>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    let id = Uuid::new_v4().to_string();
    let user_id = Uuid::new_v4().to_string(); // TODO: Extract from JWT
    let confidence = req.confidence.unwrap_or(1.0);

    let store = state.memory_store.read().await;
    store
        .save_health_data(&id, &user_id, &req.source, &req.data_type, req.value, &req.unit, confidence)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(serde_json::json!({
        "id": id,
        "source": req.source,
        "data_type": req.data_type,
        "value": req.value,
        "unit": req.unit,
        "confidence": confidence,
        "timestamp": chrono::Utc::now().to_rfc3339()
    })))
}

// ============================================================================
// Action Plans (FA-002 Agentic)
// ============================================================================

/// Action plan list query
#[derive(Deserialize)]
pub struct ActionPlanQuery {
    status: Option<String>,
    limit: Option<i32>,
}

/// List action plans
pub async fn list_action_plans(
    State(state): State<AppState>,
    Query(params): Query<ActionPlanQuery>,
) -> Json<serde_json::Value> {
    let user_id = Uuid::new_v4().to_string(); // TODO: Extract from JWT
    let limit = params.limit.unwrap_or(50);
    let store = state.memory_store.read().await;

    let plans = store
        .list_action_plans(&user_id, params.status.as_deref(), limit)
        .await
        .unwrap_or_default();

    let count = plans.len();
    Json(serde_json::json!({
        "plans": plans,
        "count": count
    }))
}

/// Create action plan request
#[derive(Deserialize)]
pub struct CreateActionPlanRequest {
    trigger: String,
    steps: Vec<serde_json::Value>,
    requires_approval: Option<bool>,
}

/// Create an action plan
pub async fn create_action_plan(
    State(state): State<AppState>,
    Json(req): Json<CreateActionPlanRequest>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    let id = Uuid::new_v4().to_string();
    let user_id = Uuid::new_v4().to_string(); // TODO: Extract from JWT
    let requires_approval = req.requires_approval.unwrap_or(true);
    let status = if requires_approval { "pending_approval" } else { "pending" };
    let steps_val = serde_json::Value::Array(req.steps.clone());

    let store = state.memory_store.read().await;
    store
        .save_action_plan(&id, &user_id, &req.trigger, status, &steps_val, requires_approval)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(serde_json::json!({
        "id": id,
        "trigger": req.trigger,
        "status": status,
        "steps": req.steps,
        "requires_approval": requires_approval,
        "created_at": chrono::Utc::now().to_rfc3339()
    })))
}

/// Approve an action plan
pub async fn approve_action_plan(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<StatusCode, StatusCode> {
    let store = state.memory_store.read().await;
    if store.update_action_plan_status(&id, "approved", Some(true))
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
    {
        Ok(StatusCode::NO_CONTENT)
    } else {
        Err(StatusCode::NOT_FOUND)
    }
}

/// Execute next step in action plan
pub async fn execute_action_plan_step(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    let store = state.memory_store.read().await;
    let plan = store
        .get_action_plan(&id)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .ok_or(StatusCode::NOT_FOUND)?;

    // Find next pending step
    let steps = plan["steps"].as_array().cloned().unwrap_or_default();
    let current_step = steps.iter().position(|s| {
        s["status"].as_str().unwrap_or("pending") == "pending"
    });

    match current_step {
        Some(idx) => {
            // Mark step as completed (in a real impl, would execute the action)
            let all_done = idx + 1 >= steps.len();
            if all_done {
                let _ = store.update_action_plan_status(&id, "completed", None).await;
            }
            Ok(Json(serde_json::json!({
                "status": "step_completed",
                "step_index": idx,
                "plan_completed": all_done,
                "message": format!("Executed step {} of {}", idx + 1, steps.len())
            })))
        }
        None => Ok(Json(serde_json::json!({
            "status": "no_pending_steps",
            "message": "All steps have been completed"
        }))),
    }
}

// ============================================================================
// Sync Trigger
// ============================================================================

/// Trigger a manual sync
pub async fn trigger_sync(
    State(state): State<AppState>,
) -> Json<serde_json::Value> {
    // Publish sync event to event bus
    let _ = state.event_bus.publish(termio_core::events::Event::new(
        termio_core::events::EventPayload::Sync(
            termio_core::events::SyncEvent::SyncStarted,
        ),
        "sync_handler",
    ));

    Json(serde_json::json!({
        "status": "sync_initiated",
        "timestamp": chrono::Utc::now().to_rfc3339()
    }))
}

// --- New Feature Handlers (Subscriptions, Payments, Smart Home) ---
use termio_core::models::subscription::{Subscription, SubscriptionTier, SubscriptionStatus, PaymentProvider};
use termio_core::payments::{StripeWebhookPayload, BinanceWebhookPayload, PaymentProcessor};
use termio_core::models::smart_home::{SmartDevice, HomeScene};

#[derive(Serialize)]
pub struct SubscriptionPlan {
    pub id: String,
    pub name: String,
    pub tier: String,
    pub price_monthly: f64,
    pub price_yearly: f64,
    pub features: Vec<String>,
    pub device_limit: i32,
    pub model_limit_gb: i32,
}

pub async fn get_subscription(State(state): State<AppState>) -> Result<Json<Subscription>, StatusCode> {
    let user_id = "default-user".to_string();
    
    let store = state.memory_store.read().await;
    match store.get_subscription(&user_id).await {
        Ok(Some(sub)) => Ok(Json(sub)),
        Ok(None) => {
            let default_sub = Subscription {
                id: uuid::Uuid::new_v4(),
                user_id: uuid::Uuid::new_v4(),
                tier: SubscriptionTier::Freemium,
                status: SubscriptionStatus::Active,
                provider: PaymentProvider::Manual,
                provider_subscription_id: None,
                start_date: chrono::Utc::now(),
                end_date: chrono::Utc::now() + chrono::Duration::days(365),
                auto_renew: false,
                features: serde_json::json!({
                    "core_assistant": true,
                    "multi_modal_input": true,
                    "hybrid_ai_inference": "local_only",
                    "memory_system": "ring_buffer_only",
                    "plugin_ecosystem": false,
                    "devices": 1,
                    "support": "community"
                }),
            };
            Ok(Json(default_sub))
        }
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

#[derive(Deserialize)]
pub struct UpdateSubscriptionRequest {
    tier: String,
}

pub async fn update_subscription(
    State(state): State<AppState>,
    Json(payload): Json<UpdateSubscriptionRequest>,
) -> Result<Json<Subscription>, StatusCode> {
    let user_id = "default-user".to_string();
    
    let tier = match payload.tier.to_lowercase().as_str() {
        "freemium" => SubscriptionTier::Freemium,
        "pro" => SubscriptionTier::Pro,
        "business" => SubscriptionTier::Business,
        "enterprise" => SubscriptionTier::Enterprise,
        _ => return Err(StatusCode::BAD_REQUEST),
    };
    
    let store = state.memory_store.read().await;
    
    let subscription = Subscription {
        id: uuid::Uuid::new_v4(),
        user_id: uuid::Uuid::new_v4(),
        tier,
        status: SubscriptionStatus::Active,
        provider: PaymentProvider::Stripe,
        provider_subscription_id: None,
        start_date: chrono::Utc::now(),
        end_date: chrono::Utc::now() + chrono::Duration::days(30),
        auto_renew: true,
        features: serde_json::json!({}),
    };
    
    if let Err(_) = store.save_subscription(&subscription).await {
        return Err(StatusCode::INTERNAL_SERVER_ERROR);
    }
    
    Ok(Json(subscription))
}

pub async fn list_plans(State(_state): State<AppState>) -> Result<Json<Vec<SubscriptionPlan>>, StatusCode> {
    let plans = vec![
        SubscriptionPlan {
            id: "freemium".to_string(),
            name: "Freemium".to_string(),
            tier: "freemium".to_string(),
            price_monthly: 0.0,
            price_yearly: 0.0,
            features: vec![
                "Core AI assistant".to_string(),
                "Local-only AI inference".to_string(),
                "Ring buffer memory (100 interactions)".to_string(),
                "1 device".to_string(),
                "Community support".to_string(),
            ],
            device_limit: 1,
            model_limit_gb: 2,
        },
        SubscriptionPlan {
            id: "pro".to_string(),
            name: "Pro".to_string(),
            tier: "pro".to_string(),
            price_monthly: 9.99,
            price_yearly: 99.99,
            features: vec![
                "Everything in Freemium".to_string(),
                "Cloud augmentation".to_string(),
                "Full memory system (vector + graph)".to_string(),
                "Plugin ecosystem".to_string(),
                "Agentic OS".to_string(),
                "Visual intelligence".to_string(),
                "Proactive thinker".to_string(),
                "Smart home control".to_string(),
                "Cross-device sync".to_string(),
                "Up to 5 devices".to_string(),
                "Priority email support".to_string(),
            ],
            device_limit: 5,
            model_limit_gb: 4,
        },
        SubscriptionPlan {
            id: "business".to_string(),
            name: "Business".to_string(),
            tier: "business".to_string(),
            price_monthly: 29.99,
            price_yearly: 299.99,
            features: vec![
                "Everything in Pro".to_string(),
                "Health monitoring".to_string(),
                "Team collaboration".to_string(),
                "Audit logs".to_string(),
                "Unlimited devices".to_string(),
                "24/7 priority support".to_string(),
            ],
            device_limit: -1,
            model_limit_gb: 4,
        },
        SubscriptionPlan {
            id: "enterprise".to_string(),
            name: "Enterprise".to_string(),
            tier: "enterprise".to_string(),
            price_monthly: 0.0,
            price_yearly: 0.0,
            features: vec![
                "Everything in Business".to_string(),
                "On-premise deployment".to_string(),
                "Custom models".to_string(),
                "SSO integration (SAML, OIDC)".to_string(),
                "HIPAA, GDPR, SOC2 compliance".to_string(),
                "Dedicated account manager".to_string(),
                "24/7 phone support".to_string(),
            ],
            device_limit: -1,
            model_limit_gb: -1,
        },
    ];
    
    Ok(Json(plans))
}

pub async fn stripe_webhook(State(_state): State<AppState>, Json(payload): Json<StripeWebhookPayload>) -> Result<StatusCode, StatusCode> {
    PaymentProcessor::process_stripe_webhook(&payload).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    Ok(StatusCode::OK)
}

pub async fn binance_webhook(State(_state): State<AppState>, Json(payload): Json<BinanceWebhookPayload>) -> Result<StatusCode, StatusCode> {
    PaymentProcessor::process_binance_webhook(&payload).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    Ok(StatusCode::OK)
}

pub async fn list_devices(State(state): State<AppState>) -> Result<Json<Vec<SmartDevice>>, StatusCode> {
    let user_id = "default-user".to_string();
    let store = state.memory_store.read().await;
    
    match store.list_smart_devices(&user_id).await {
        Ok(devices) => Ok(Json(devices)),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

#[derive(Deserialize)]
pub struct AddDeviceRequest {
    name: String,
    device_type: String,
    protocol: Option<String>,
    state: Option<serde_json::Value>,
}

pub async fn add_device(State(state): State<AppState>, Json(req): Json<AddDeviceRequest>) -> Result<Json<SmartDevice>, StatusCode> {
    let user_id = uuid::Uuid::new_v4();
    
    let device_type = match req.device_type.to_lowercase().as_str() {
        "light" => termio_core::models::smart_home::DeviceType::Light,
        "thermostat" => termio_core::models::smart_home::DeviceType::Thermostat,
        "lock" => termio_core::models::smart_home::DeviceType::Lock,
        "camera" => termio_core::models::smart_home::DeviceType::Camera,
        "sensor" => termio_core::models::smart_home::DeviceType::Sensor,
        "speaker" => termio_core::models::smart_home::DeviceType::Speaker,
        other => termio_core::models::smart_home::DeviceType::Unknown(other.to_string()),
    };
    
    let device = SmartDevice {
        id: uuid::Uuid::new_v4(),
        user_id,
        name: req.name,
        device_type,
        protocol: req.protocol.unwrap_or_else(|| "matter".to_string()),
        is_online: true,
        state: req.state.unwrap_or_default(),
    };
    
    let store = state.memory_store.read().await;
    if let Err(_) = store.save_smart_device(&device).await {
        return Err(StatusCode::INTERNAL_SERVER_ERROR);
    }
    
    Ok(Json(device))
}

pub async fn update_device_state(
    State(state): State<AppState>,
    axum::extract::Path(id): axum::extract::Path<uuid::Uuid>,
    Json(state_payload): Json<serde_json::Value>,
) -> Result<StatusCode, StatusCode> {
    let store = state.memory_store.read().await;
    
    match store.update_smart_device_state(&id.to_string(), &state_payload).await {
        Ok(true) => Ok(StatusCode::NO_CONTENT),
        Ok(false) => Err(StatusCode::NOT_FOUND),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

pub async fn list_scenes(State(state): State<AppState>) -> Result<Json<Vec<HomeScene>>, StatusCode> {
    let user_id = "default-user".to_string();
    let store = state.memory_store.read().await;
    
    match store.list_smart_scenes(&user_id).await {
        Ok(scenes) => Ok(Json(scenes)),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

#[derive(Deserialize)]
pub struct CreateSceneRequest {
    name: String,
    description: Option<String>,
    actions: Option<Vec<serde_json::Value>>,
}

pub async fn create_scene(State(state): State<AppState>, Json(req): Json<CreateSceneRequest>) -> Result<Json<HomeScene>, StatusCode> {
    let user_id = uuid::Uuid::new_v4();
    
    let scene = HomeScene {
        id: uuid::Uuid::new_v4(),
        user_id,
        name: req.name,
        description: req.description,
        actions: req.actions.unwrap_or_default(),
    };
    
    let store = state.memory_store.read().await;
    if let Err(_) = store.save_smart_scene(&scene).await {
        return Err(StatusCode::INTERNAL_SERVER_ERROR);
    }
    
    Ok(Json(scene))
}
