//! Health monitoring
//!
//! System health checking for CPU, memory, disk, and service availability.

mod monitor;

pub use monitor::{HealthMonitor, HealthStatus, ServiceHealth, SystemResources};
