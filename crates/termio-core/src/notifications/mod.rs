//! Notification system
//!
//! Supports system alerts, AI completions, sync events, and plugin notifications
//! with priority levels, scheduled delivery, quiet hours, and filtering.

mod manager;
mod types;

pub use manager::NotificationManager;
pub use types::{
    DeliveryChannel, Notification, NotificationCategory, NotificationFilter,
    NotificationPersonalization, NotificationPriority, NotificationStatus,
    NotificationType, QuietHours,
};
