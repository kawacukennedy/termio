//! Notification types
//!
//! Data structures for the notification system per spec schema.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Notification priority levels
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum NotificationPriority {
    Low,
    Medium,
    High,
    Critical,
}

/// Notification type per spec
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum NotificationType {
    Alert,
    Reminder,
    Suggestion,
    HealthAlert,
    System,
}

/// Notification category for filtering
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum NotificationCategory {
    System,
    Ai,
    Sync,
    Plugin,
    Memory,
    User,
    Security,
}

/// Notification delivery status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum NotificationStatus {
    Pending,
    Delivered,
    Read,
    Actioned,
}

/// Personalization context for smart notifications
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NotificationPersonalization {
    pub context: Option<String>,
    pub action_deep_link: Option<String>,
}

/// A notification entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Notification {
    pub id: Uuid,
    pub user_id: Option<Uuid>,
    pub device_id: Option<Uuid>,
    pub notification_type: NotificationType,
    pub title: String,
    pub body: String,
    pub priority: NotificationPriority,
    pub category: NotificationCategory,
    pub icon: Option<String>,
    pub data: Option<serde_json::Value>,
    pub delivery_time: Option<DateTime<Utc>>,
    pub expiration: Option<DateTime<Utc>>,
    pub status: NotificationStatus,
    pub personalization: Option<NotificationPersonalization>,
    pub created_at: DateTime<Utc>,
    pub read_at: Option<DateTime<Utc>>,
    pub read: bool,
    pub dismissed: bool,
}

impl Notification {
    /// Create a new notification
    pub fn new(
        title: impl Into<String>,
        body: impl Into<String>,
        priority: NotificationPriority,
        category: NotificationCategory,
    ) -> Self {
        Self {
            id: Uuid::new_v4(),
            user_id: None,
            device_id: None,
            notification_type: NotificationType::System,
            title: title.into(),
            body: body.into(),
            priority,
            category,
            icon: None,
            data: None,
            delivery_time: None,
            expiration: None,
            status: NotificationStatus::Pending,
            personalization: None,
            created_at: Utc::now(),
            read_at: None,
            read: false,
            dismissed: false,
        }
    }

    /// Create a system notification
    pub fn system(title: impl Into<String>, body: impl Into<String>) -> Self {
        Self::new(title, body, NotificationPriority::Medium, NotificationCategory::System)
    }

    /// Create an AI notification
    pub fn ai(title: impl Into<String>, body: impl Into<String>) -> Self {
        Self::new(title, body, NotificationPriority::Low, NotificationCategory::Ai)
    }

    /// Create a critical notification
    pub fn critical(title: impl Into<String>, body: impl Into<String>, category: NotificationCategory) -> Self {
        Self::new(title, body, NotificationPriority::Critical, category)
    }

    /// Set user and device targeting
    pub fn for_user(mut self, user_id: Uuid, device_id: Uuid) -> Self {
        self.user_id = Some(user_id);
        self.device_id = Some(device_id);
        self
    }

    /// Set notification type
    pub fn with_type(mut self, notification_type: NotificationType) -> Self {
        self.notification_type = notification_type;
        self
    }

    /// Set an icon for this notification
    pub fn with_icon(mut self, icon: impl Into<String>) -> Self {
        self.icon = Some(icon.into());
        self
    }

    /// Schedule for future delivery
    pub fn schedule(mut self, delivery_time: DateTime<Utc>) -> Self {
        self.delivery_time = Some(delivery_time);
        self
    }

    /// Set expiration
    pub fn expires_at(mut self, expiration: DateTime<Utc>) -> Self {
        self.expiration = Some(expiration);
        self
    }

    /// Add personalization context and deep link
    pub fn with_personalization(mut self, context: impl Into<String>, deep_link: Option<String>) -> Self {
        self.personalization = Some(NotificationPersonalization {
            context: Some(context.into()),
            action_deep_link: deep_link,
        });
        self
    }

    /// Check if notification has expired
    pub fn is_expired(&self) -> bool {
        self.expiration.map_or(false, |exp| Utc::now() > exp)
    }

    /// Check if ready for delivery
    pub fn is_ready_for_delivery(&self) -> bool {
        if self.is_expired() { return false; }
        self.delivery_time.map_or(true, |dt| Utc::now() >= dt)
    }

    /// Mark as delivered
    pub fn deliver(&mut self) {
        self.status = NotificationStatus::Delivered;
    }

    /// Mark as read
    pub fn mark_read(&mut self) {
        self.read = true;
        self.status = NotificationStatus::Read;
        self.read_at = Some(Utc::now());
    }

    /// Mark as dismissed
    pub fn dismiss(&mut self) {
        self.dismissed = true;
        self.read = true;
    }

    /// Mark as actioned
    pub fn action(&mut self) {
        self.status = NotificationStatus::Actioned;
    }

    /// Check if notification is active
    pub fn is_active(&self) -> bool {
        !self.read && !self.dismissed && !self.is_expired()
    }

    /// Check if notification matches a filter
    pub fn matches_filter(&self, filter: &NotificationFilter) -> bool {
        if let Some(ref status) = filter.status {
            if self.status != *status {
                return false;
            }
        }
        if let Some(ref priority) = filter.min_priority {
            if self.priority < *priority {
                return false;
            }
        }
        if let Some(ref category) = filter.category {
            if self.category != *category {
                return false;
            }
        }
        if filter.unread_only && self.read {
            return false;
        }
        if filter.exclude_dismissed && self.dismissed {
            return false;
        }
        if filter.exclude_expired && self.is_expired() {
            return false;
        }
        true
    }
}

/// Filter for querying notifications
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct NotificationFilter {
    /// Filter by status
    pub status: Option<NotificationStatus>,
    /// Filter by minimum priority
    pub min_priority: Option<NotificationPriority>,
    /// Filter by category
    pub category: Option<NotificationCategory>,
    /// Only show unread
    pub unread_only: bool,
    /// Exclude dismissed notifications
    pub exclude_dismissed: bool,
    /// Exclude expired notifications
    pub exclude_expired: bool,
}

impl NotificationFilter {
    pub fn unread() -> Self {
        Self {
            unread_only: true,
            exclude_dismissed: true,
            exclude_expired: true,
            ..Default::default()
        }
    }

    pub fn active() -> Self {
        Self {
            exclude_dismissed: true,
            exclude_expired: true,
            ..Default::default()
        }
    }
}

/// User-configurable quiet hours
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuietHours {
    /// Whether quiet hours are enabled
    pub enabled: bool,
    /// Start hour (0-23)
    pub start_hour: u8,
    /// End hour (0-23)
    pub end_hour: u8,
    /// Allow critical notifications during quiet hours
    pub allow_critical: bool,
}

impl Default for QuietHours {
    fn default() -> Self {
        Self {
            enabled: false,
            start_hour: 22,
            end_hour: 7,
            allow_critical: true,
        }
    }
}

impl QuietHours {
    /// Check if the current time is within quiet hours
    pub fn is_quiet_now(&self) -> bool {
        if !self.enabled {
            return false;
        }
        let hour = Utc::now().format("%H").to_string().parse::<u8>().unwrap_or(0);
        if self.start_hour <= self.end_hour {
            hour >= self.start_hour && hour < self.end_hour
        } else {
            hour >= self.start_hour || hour < self.end_hour
        }
    }

    /// Check if a notification should be delivered during quiet hours
    pub fn should_deliver(&self, priority: &NotificationPriority) -> bool {
        if !self.is_quiet_now() {
            return true;
        }
        self.allow_critical && *priority == NotificationPriority::Critical
    }
}

/// Delivery channel for notifications
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DeliveryChannel {
    /// Push to mobile device
    Mobile,
    /// Desktop notification
    Desktop,
    /// TUI notification panel
    Terminal,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_notification_creation() {
        let notif = Notification::system("Test", "Test body");
        assert_eq!(notif.title, "Test");
        assert_eq!(notif.priority, NotificationPriority::Medium);
        assert_eq!(notif.category, NotificationCategory::System);
        assert!(!notif.read);
        assert!(!notif.dismissed);
        assert_eq!(notif.status, NotificationStatus::Pending);
    }

    #[test]
    fn test_notification_lifecycle() {
        let mut notif = Notification::system("Test", "Test body")
            .for_user(Uuid::new_v4(), Uuid::new_v4())
            .with_type(NotificationType::Alert);

        notif.deliver();
        assert_eq!(notif.status, NotificationStatus::Delivered);

        notif.mark_read();
        assert!(notif.read);
        assert!(notif.read_at.is_some());
        assert_eq!(notif.status, NotificationStatus::Read);
    }

    #[test]
    fn test_notification_dismiss() {
        let mut notif = Notification::system("Test", "Test body");
        notif.dismiss();
        assert!(notif.read);
        assert!(notif.dismissed);
    }

    #[test]
    fn test_priority_ordering() {
        assert!(NotificationPriority::Low < NotificationPriority::Critical);
        assert!(NotificationPriority::Medium < NotificationPriority::High);
    }

    #[test]
    fn test_notification_filter() {
        let notif = Notification::system("Test", "body");
        let filter = NotificationFilter::unread();
        assert!(notif.matches_filter(&filter));

        let mut read_notif = Notification::system("Test", "body");
        read_notif.mark_read();
        assert!(!read_notif.matches_filter(&filter));
    }

    #[test]
    fn test_quiet_hours_default() {
        let qh = QuietHours::default();
        assert!(!qh.enabled);
        assert!(qh.allow_critical);
    }
}

