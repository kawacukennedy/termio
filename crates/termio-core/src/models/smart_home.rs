//! Smart home integration model
//!
//! IoT device management and scene automation (FA-006).
//!
//! ## Overview
//!
//! TERMIO integrates with smart home ecosystems via Matter, the universal
//! smart home protocol. This enables voice control and automation of:
//! - Lighting (on/off, brightness, color)
//! - Climate (thermostats, AC)
//! - Security (locks, cameras, sensors)
//! - Audio (speakers, multi-room)
//!
//! ## Supported Protocols
//!
//! | Protocol | Description | Matter Support |
//! |----------|-------------|----------------|
//! | matter | Universal standard | Native |
//! | thread | Low-power mesh | Via Matter |
//! | zigbee | Legacy mesh | Bridge required |
//! | zwave | Legacy mesh | Bridge required |
//!
//! ## Device State
//!
//! Device state is stored as JSON for protocol-agnostic handling:
//!
//! ```json
//! {"on": true, "brightness": 75, "color": {"r": 255, "g": 200, "b": 100}}
//! ```
//!
//! ## Scenes
//!
//! Scenes group multiple device actions:
//!
//! ```rust
//! let movie_night = HomeScene {
//!     name: "Movie Night".into(),
//!     actions: vec![
//!         json!({"device": "living_room_lights", "action": "dim", "value": 20}),
//!         json!({"device": "tv", "action": "power", "value": true}),
//!     ],
//! };
//! ```

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
    pub protocol: String,
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
