use serde::{Deserialize, Serialize};
use tauri::Manager;

#[derive(Debug, Serialize, Deserialize)]
pub struct Message {
    pub id: String,
    pub role: String,
    pub content: String,
    pub timestamp: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Conversation {
    pub id: String,
    pub messages: Vec<Message>,
}

#[tauri::command]
async fn send_message(
    message: String,
    server_url: String,
) -> Result<String, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .post(format!("{}/api/ai/chat", server_url))
        .json(&serde_json::json!({ "message": message }))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        let body: serde_json::Value = response.json().await.map_err(|e| e.to_string())?;
        Ok(body["response"].as_str().unwrap_or("").to_string())
    } else {
        Err(format!("Server error: {}", response.status()))
    }
}

#[tauri::command]
async fn get_conversations(server_url: String) -> Result<Vec<Conversation>, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .get(format!("{}/api/conversations", server_url))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        let body: serde_json::Value = response.json().await.map_err(|e| e.to_string())?;
        let convs = body["conversations"].as_array()
            .ok_or("Invalid response")?
            .iter()
            .map(|c| Conversation {
                id: c["id"].as_str().unwrap_or("").to_string(),
                messages: vec![],
            })
            .collect();
        Ok(convs)
    } else {
        Err(format!("Server error: {}", response.status()))
    }
}

#[tauri::command]
async fn get_notifications(server_url: String) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .get(format!("{}/api/notifications", server_url))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        response.json().await.map_err(|e| e.to_string())
    } else {
        Err(format!("Server error: {}", response.status()))
    }
}

#[tauri::command]
async fn get_sync_status(server_url: String) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .get(format!("{}/api/sync/status", server_url))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        response.json().await.map_err(|e| e.to_string())
    } else {
        Err(format!("Server error: {}", response.status()))
    }
}

#[tauri::command]
async fn trigger_sync(server_url: String) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .post(format!("{}/api/sync/trigger", server_url))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        response.json().await.map_err(|e| e.to_string())
    } else {
        Err(format!("Server error: {}", response.status()))
    }
}

#[tauri::command]
async fn list_plugins(server_url: String) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .get(format!("{}/api/plugins", server_url))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if response.status().is_success() {
        response.json().await.map_err(|e| e.to_string())
    } else {
        Err(format!("Server error: {}", response.status()))
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::INFO.into()),
        )
        .init();

    tracing::info!("Starting TERMIO Desktop...");

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            send_message,
            get_conversations,
            get_notifications,
            get_sync_status,
            trigger_sync,
            list_plugins,
        ])
        .setup(|app| {
            let window = app.get_webview_window("main").unwrap();
            window.set_title("TERMIO").unwrap();
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
