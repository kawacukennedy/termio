use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum DeviceType {
    Light,
    Thermostat,
    Lock,
    Camera,
    Sensor,
    Speaker,
    Unknown(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SmartDevice {
    pub id: Uuid,
    pub user_id: Uuid,
    pub name: String,
    pub device_type: DeviceType,
    pub protocol: String, // "matter", "thread", etc.
    pub is_online: bool,
    pub state: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HomeScene {
    pub id: Uuid,
    pub user_id: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub actions: Vec<serde_json::Value>, 
}
