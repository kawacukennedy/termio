//! Health monitoring
//!
//! System health checking for CPU, memory, disk, and service availability.
//!
//! # Health Status
//!
//! - **Healthy**: All systems operational
//! - **Degraded**: Some services unavailable
//! - **Unhealthy**: Critical systems down (e.g., database)
//!
//! # System Resources
//!
//! - Uptime: Time since process started
//! - Memory: Process memory usage
//! - Database: Connection status
//!
//! # Service Health
//!
//! Individual services can report their health status:
//! - AI inference service
//! - Memory store
//! - Sync engine
//! - Notification delivery
//!
//! # Usage
//!
//! ```rust
//! use termio_core::health::{HealthMonitor, HealthStatus};
//!
//! let monitor = HealthMonitor::new("http://localhost:8000");
//!
//! // Check AI service
//! let ai_health = HealthMonitor::check_service(
//!     "ai_inference",
//!     true,           // available
//!     Some(50),       // response time ms
//!     None            // message
//! );
//!
//! // Generate full report
//! let report = monitor.report(true, vec![ai_health]);
//! println!("Status: {:?}", report.status);
//! ```

mod monitor;

pub use monitor::{HealthMonitor, HealthStatus, ServiceHealth, SystemResources};
