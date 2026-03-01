//! Notification system
//!
//! Supports system alerts, AI completions, sync events, and plugin notifications
//! with priority levels, scheduled delivery, quiet hours, and filtering.
//!
//! # Features
//!
//! - **Priority Levels**: Low, Medium, High, Critical
//! - **Categories**: System, AI, Sync, Plugin, Memory, User, Security
//! - **Delivery Status**: Pending, Delivered, Read, Actioned
//! - **Quiet Hours**: Suppress non-critical notifications during configured times
//! - **Scheduling**: Future delivery with delivery_time
//! - **Expiration**: Auto-expire old notifications
//! - **Filtering**: Query by status, priority, category
//!
//! # Usage
//!
//! ```rust
//! use termio_core::notifications::{Notification, NotificationPriority, NotificationCategory};
//!
//! // Create notification
//! let notif = Notification::system("Title", "Body");
//!
// manager.notify(notif);
//! ```

mod manager;
mod types;

pub use manager::NotificationManager;
pub use types::{
    DeliveryChannel, Notification, NotificationCategory, NotificationFilter,
    NotificationPersonalization, NotificationPriority, NotificationStatus,
    NotificationType, QuietHours,
};
