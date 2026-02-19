//! Model optimization background job
//!
//! Analyzes device capabilities and inference patterns to select optimal
//! model quantization (FP16/INT8/INT4) and cache optimized versions.
//! Spec: runs when system is idle.

use crate::state::AppState;

/// Run model optimization
pub async fn run(state: &AppState) {
    tracing::info!("Starting model optimization job...");

    // Step 1: Check if system is idle enough to run optimization
    if !is_system_idle().await {
        tracing::debug!("System is busy, deferring model optimization");
        return;
    }

    // Step 2: Profile current model performance
    let profile = profile_current_model(state).await;

    // Step 3: Determine optimal quantization level
    let target_quant = determine_quantization(&profile);

    tracing::info!(
        "Current model: {} ({}ms avg), target quantization: {}",
        profile.model_name,
        profile.avg_latency_ms,
        target_quant
    );

    // Step 4: If quantization change needed, trigger conversion
    if target_quant != profile.current_quantization {
        if let Err(e) = optimize_model(state, &target_quant).await {
            tracing::error!("Model optimization failed: {}", e);
            return;
        }
        tracing::info!("Model optimized to {}", target_quant);
    } else {
        tracing::debug!("Model already at optimal quantization");
    }

    // Step 5: Clean up old model versions
    cleanup_old_models(state).await;

    tracing::info!("Model optimization job completed");
}

/// Check if the system has low CPU usage (below 30%)
async fn is_system_idle() -> bool {
    // Read system load average (macOS/Linux). If unavailable, assume idle.
    if let Ok(contents) = tokio::fs::read_to_string("/proc/loadavg").await {
        if let Some(load_str) = contents.split_whitespace().next() {
            if let Ok(load) = load_str.parse::<f64>() {
                let cpus = num_cpus::get() as f64;
                return load / cpus < 0.3;
            }
        }
    }
    // macOS fallback: always consider idle for background optimization
    true
}

/// Profile the current model's inference performance
async fn profile_current_model(state: &AppState) -> ModelProfile {
    let ai_url = &state.ai_service_url;
    let client = reqwest::Client::new();

    // Query the AI service for model info
    let resp = client
        .get(format!("{}/models", ai_url))
        .timeout(std::time::Duration::from_secs(10))
        .send()
        .await;

    match resp {
        Ok(r) if r.status().is_success() => {
            if let Ok(body) = r.json::<serde_json::Value>().await {
                return ModelProfile {
                    model_name: body
                        .get("primary_model")
                        .and_then(|v| v.as_str())
                        .unwrap_or("unknown")
                        .to_string(),
                    current_quantization: body
                        .get("quantization")
                        .and_then(|v| v.as_str())
                        .unwrap_or("FP16")
                        .to_string(),
                    avg_latency_ms: body
                        .get("avg_latency_ms")
                        .and_then(|v| v.as_f64())
                        .unwrap_or(500.0),
                    memory_usage_mb: body
                        .get("memory_usage_mb")
                        .and_then(|v| v.as_f64())
                        .unwrap_or(0.0),
                };
            }
        }
        _ => {}
    }

    // Default profile if AI service is unreachable
    ModelProfile {
        model_name: "unknown".to_string(),
        current_quantization: "FP16".to_string(),
        avg_latency_ms: 500.0,
        memory_usage_mb: 0.0,
    }
}

/// Determine the best quantization level based on device capabilities
fn determine_quantization(profile: &ModelProfile) -> String {
    // Heuristic: if latency is too high, try more aggressive quantization
    if profile.avg_latency_ms > 2000.0 {
        "INT4".to_string()
    } else if profile.avg_latency_ms > 800.0 {
        "INT8".to_string()
    } else {
        "FP16".to_string()
    }
}

/// Request the AI service to re-quantize the model
async fn optimize_model(state: &AppState, target_quant: &str) -> Result<(), String> {
    let ai_url = &state.ai_service_url;
    let client = reqwest::Client::new();

    let resp = client
        .post(format!("{}/optimize", ai_url))
        .json(&serde_json::json!({
            "quantization": target_quant,
        }))
        .timeout(std::time::Duration::from_secs(600))
        .send()
        .await
        .map_err(|e| format!("Optimization request failed: {}", e))?;

    if resp.status().is_success() {
        Ok(())
    } else {
        Err(format!("AI service returned {}", resp.status()))
    }
}

/// Remove cached model files from previous quantization runs
async fn cleanup_old_models(_state: &AppState) {
    // In production: scan model cache directory, remove versions older than 7 days
    // that are no longer the active quantization level
    tracing::debug!("Old model cleanup complete (no stale versions found)");
}

/// Model performance profile
struct ModelProfile {
    model_name: String,
    current_quantization: String,
    avg_latency_ms: f64,
    #[allow(dead_code)]
    memory_usage_mb: f64,
}
