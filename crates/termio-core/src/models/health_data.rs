//! Health & biometric data model
//!
//! Tracks health data from wearables, manual input, and device sensors.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Source of health data
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum HealthDataSource {
    Wearable,
    Manual,
    DeviceSensors,
}

/// Type of health measurement
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum HealthDataType {
    HeartRate,
    Hrv,
    Spo2,
    SkinTemperature,
    Steps,
    Sleep,
    Stress,
}

/// Metadata about the health data reading
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthDataMetadata {
    pub device_model: Option<String>,
    pub session_id: Option<String>,
}

/// A single health data entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthData {
    pub id: Uuid,
    pub user_id: Uuid,
    pub source: HealthDataSource,
    pub timestamp: DateTime<Utc>,
    pub data_type: HealthDataType,
    pub value: f64,
    pub unit: String,
    pub confidence: f64,
    pub metadata: HealthDataMetadata,
}

impl HealthData {
    pub fn new(
        user_id: Uuid,
        source: HealthDataSource,
        data_type: HealthDataType,
        value: f64,
        unit: impl Into<String>,
    ) -> Self {
        Self {
            id: Uuid::new_v4(),
            user_id,
            source,
            timestamp: Utc::now(),
            data_type,
            value,
            unit: unit.into(),
            confidence: 1.0,
            metadata: HealthDataMetadata {
                device_model: None,
                session_id: None,
            },
        }
    }

    pub fn with_confidence(mut self, confidence: f64) -> Self {
        self.confidence = confidence.clamp(0.0, 1.0);
        self
    }

    pub fn with_device(mut self, model: impl Into<String>) -> Self {
        self.metadata.device_model = Some(model.into());
        self
    }
}