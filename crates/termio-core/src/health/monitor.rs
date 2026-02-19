//! Health monitor
//!
//! Checks system resources and service availability.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::time::Instant;

/// Overall health status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum HealthStatus {
    /// All systems operational
    Healthy,
    /// Some systems degraded
    Degraded,
    /// Critical issues
    Unhealthy,
}

/// System resource information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemResources {
    /// Uptime in seconds
    pub uptime_secs: u64,
    /// Memory usage estimate (bytes in use by the process)
    pub memory_usage_bytes: u64,
    /// Whether the database is accessible
    pub database_connected: bool,
}

/// Individual service health
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceHealth {
    /// Service name
    pub name: String,
    /// Whether the service is available
    pub available: bool,
    /// Last check timestamp
    pub last_check: DateTime<Utc>,
    /// Response time in ms (None if unavailable)
    pub response_time_ms: Option<u64>,
    /// Optional status message
    pub message: Option<String>,
}

/// Health report combining all checks
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthReport {
    /// Overall status
    pub status: HealthStatus,
    /// System resource info
    pub resources: SystemResources,
    /// Individual service health checks
    pub services: Vec<ServiceHealth>,
    /// When this report was generated
    pub timestamp: DateTime<Utc>,
}

/// Health monitor
pub struct HealthMonitor {
    start_time: Instant,
    ai_service_url: String,
}

impl HealthMonitor {
    /// Create a new health monitor
    pub fn new(ai_service_url: impl Into<String>) -> Self {
        Self {
            start_time: Instant::now(),
            ai_service_url: ai_service_url.into(),
        }
    }

    /// Get system uptime
    pub fn uptime_secs(&self) -> u64 {
        self.start_time.elapsed().as_secs()
    }

    /// Get system resources
    pub fn system_resources(&self, db_connected: bool) -> SystemResources {
        SystemResources {
            uptime_secs: self.uptime_secs(),
            memory_usage_bytes: 0, // Would use sysinfo crate in production
            database_connected: db_connected,
        }
    }

    /// Build a health report
    pub fn report(&self, db_connected: bool, services: Vec<ServiceHealth>) -> HealthReport {
        let resources = self.system_resources(db_connected);

        let status = if !db_connected {
            HealthStatus::Unhealthy
        } else if services.iter().any(|s| !s.available) {
            HealthStatus::Degraded
        } else {
            HealthStatus::Healthy
        };

        HealthReport {
            status,
            resources,
            services,
            timestamp: Utc::now(),
        }
    }

    /// Create a service health entry
    pub fn check_service(
        name: impl Into<String>,
        available: bool,
        response_time_ms: Option<u64>,
        message: Option<String>,
    ) -> ServiceHealth {
        ServiceHealth {
            name: name.into(),
            available,
            last_check: Utc::now(),
            response_time_ms,
            message,
        }
    }

    /// Get the AI service URL for health checking
    pub fn ai_service_url(&self) -> &str {
        &self.ai_service_url
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_health_monitor() {
        let monitor = HealthMonitor::new("http://localhost:8000");
        assert!(monitor.uptime_secs() < 2);

        let resources = monitor.system_resources(true);
        assert!(resources.database_connected);
    }

    #[test]
    fn test_health_report_status() {
        let monitor = HealthMonitor::new("http://localhost:8000");

        // Healthy when all services available and DB connected
        let services = vec![
            HealthMonitor::check_service("ai", true, Some(50), None),
        ];
        let report = monitor.report(true, services);
        assert_eq!(report.status, HealthStatus::Healthy);

        // Degraded when a service is unavailable but DB connected
        let services = vec![
            HealthMonitor::check_service("ai", false, None, Some("Offline".into())),
        ];
        let report = monitor.report(true, services);
        assert_eq!(report.status, HealthStatus::Degraded);

        // Unhealthy when DB disconnected
        let report = monitor.report(false, vec![]);
        assert_eq!(report.status, HealthStatus::Unhealthy);
    }
}
