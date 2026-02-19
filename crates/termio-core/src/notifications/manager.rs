//! Notification manager
//!
//! Manages notification lifecycle: create, schedule, read, dismiss, clear.
//! Supports quiet hours, expiration, and filtering.

use std::sync::{Arc, Mutex};
use chrono::{DateTime, Utc};
use uuid::Uuid;

use super::types::{
    Notification, NotificationCategory, NotificationFilter,
    NotificationPriority, QuietHours,
};

/// Manages the notification queue
#[derive(Clone)]
pub struct NotificationManager {
    notifications: Arc<Mutex<Vec<Notification>>>,
    max_notifications: usize,
    quiet_hours: Arc<Mutex<QuietHours>>,
}

impl NotificationManager {
    /// Create a new notification manager
    pub fn new(max_notifications: usize) -> Self {
        Self {
            notifications: Arc::new(Mutex::new(Vec::new())),
            max_notifications,
            quiet_hours: Arc::new(Mutex::new(QuietHours::default())),
        }
    }

    /// Add a notification (immediate delivery)
    pub fn notify(&self, notification: Notification) {
        let quiet = self.quiet_hours.lock().unwrap();
        if !quiet.should_deliver(&notification.priority) {
            // During quiet hours, only critical notifications are delivered
            return;
        }
        drop(quiet);

        let mut notifs = self.notifications.lock().unwrap();
        self.enforce_limit(&mut notifs);
        notifs.push(notification);
    }

    /// Schedule a notification for future delivery
    pub fn schedule_notification(
        &self,
        notification: Notification,
    ) {
        // Scheduled notifications are stored immediately but not yet "delivered"
        let mut notifs = self.notifications.lock().unwrap();
        self.enforce_limit(&mut notifs);
        notifs.push(notification);
    }

    /// Deliver all notifications whose delivery_time has arrived
    pub fn deliver_ready(&self) -> Vec<Uuid> {
        let mut notifs = self.notifications.lock().unwrap();
        let quiet = self.quiet_hours.lock().unwrap();
        let mut delivered = Vec::new();

        for notif in notifs.iter_mut() {
            if notif.is_ready_for_delivery()
                && notif.status == super::types::NotificationStatus::Pending
                && quiet.should_deliver(&notif.priority)
            {
                notif.deliver();
                delivered.push(notif.id);
            }
        }

        delivered
    }

    /// Check and remove expired notifications
    pub fn check_expirations(&self) -> usize {
        let mut notifs = self.notifications.lock().unwrap();
        let before = notifs.len();
        notifs.retain(|n| !n.is_expired());
        before - notifs.len()
    }

    /// Get all unread notifications
    pub fn unread(&self) -> Vec<Notification> {
        let notifs = self.notifications.lock().unwrap();
        notifs.iter().filter(|n| !n.read && !n.dismissed).cloned().collect()
    }

    /// Get unread count
    pub fn unread_count(&self) -> usize {
        let notifs = self.notifications.lock().unwrap();
        notifs.iter().filter(|n| !n.read && !n.dismissed).count()
    }

    /// Get all notifications (including read/dismissed)
    pub fn all(&self) -> Vec<Notification> {
        let notifs = self.notifications.lock().unwrap();
        notifs.clone()
    }

    /// Get notifications by category
    pub fn by_category(&self, category: NotificationCategory) -> Vec<Notification> {
        let notifs = self.notifications.lock().unwrap();
        notifs.iter().filter(|n| n.category == category && !n.dismissed).cloned().collect()
    }

    /// Filter notifications using a NotificationFilter
    pub fn filter(&self, filter: &NotificationFilter) -> Vec<Notification> {
        let notifs = self.notifications.lock().unwrap();
        notifs.iter().filter(|n| n.matches_filter(filter)).cloned().collect()
    }

    /// Get a notification by ID
    pub fn get_by_id(&self, id: Uuid) -> Option<Notification> {
        let notifs = self.notifications.lock().unwrap();
        notifs.iter().find(|n| n.id == id).cloned()
    }

    /// Mark a notification as read
    pub fn mark_read(&self, id: Uuid) -> bool {
        let mut notifs = self.notifications.lock().unwrap();
        if let Some(notif) = notifs.iter_mut().find(|n| n.id == id) {
            notif.mark_read();
            true
        } else {
            false
        }
    }

    /// Dismiss a notification
    pub fn dismiss(&self, id: Uuid) -> bool {
        let mut notifs = self.notifications.lock().unwrap();
        if let Some(notif) = notifs.iter_mut().find(|n| n.id == id) {
            notif.dismiss();
            true
        } else {
            false
        }
    }

    /// Dismiss all notifications
    pub fn dismiss_all(&self) {
        let mut notifs = self.notifications.lock().unwrap();
        for notif in notifs.iter_mut() {
            notif.dismiss();
        }
    }

    /// Clear all dismissed notifications
    pub fn clear_dismissed(&self) {
        let mut notifs = self.notifications.lock().unwrap();
        notifs.retain(|n| !n.dismissed);
    }

    /// Set quiet hours configuration
    pub fn set_quiet_hours(&self, qh: QuietHours) {
        let mut quiet = self.quiet_hours.lock().unwrap();
        *quiet = qh;
    }

    /// Get quiet hours configuration
    pub fn get_quiet_hours(&self) -> QuietHours {
        self.quiet_hours.lock().unwrap().clone()
    }

    /// Persist notifications to database (stub — real impl uses sqlx)
    pub fn persist_to_db(&self) -> Result<usize, String> {
        let notifs = self.notifications.lock().unwrap();
        // In a real implementation, this would INSERT/UPDATE rows in the
        // notifications table via sqlx.
        tracing::info!("Persisting {} notifications to database", notifs.len());
        Ok(notifs.len())
    }

    /// Load notifications from database (stub — real impl uses sqlx)
    pub fn load_from_db(&self) -> Result<usize, String> {
        // In a real implementation, this would SELECT from the notifications
        // table and populate the in-memory store.
        tracing::info!("Loading notifications from database");
        Ok(0)
    }

    /// Enforce max limit, evicting oldest non-critical dismissed first
    fn enforce_limit(&self, notifs: &mut Vec<Notification>) {
        while notifs.len() >= self.max_notifications {
            if let Some(pos) = notifs.iter().position(|n| {
                n.priority != NotificationPriority::Critical && n.dismissed
            }) {
                notifs.remove(pos);
            } else if let Some(pos) = notifs.iter().position(|n| {
                n.priority != NotificationPriority::Critical
            }) {
                notifs.remove(pos);
            } else {
                notifs.remove(0);
            }
        }
    }
}

impl Default for NotificationManager {
    fn default() -> Self {
        Self::new(200)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_notification_lifecycle() {
        let manager = NotificationManager::new(100);

        // Add notification
        let notif = Notification::system("Test Title", "Test body");
        let id = notif.id;
        manager.notify(notif);

        assert_eq!(manager.unread_count(), 1);

        // Mark read
        assert!(manager.mark_read(id));
        assert_eq!(manager.unread_count(), 0);

        // Dismiss
        assert!(manager.dismiss(id));
        assert_eq!(manager.all().len(), 1);

        // Clear dismissed
        manager.clear_dismissed();
        assert_eq!(manager.all().len(), 0);
    }

    #[test]
    fn test_max_limit() {
        let manager = NotificationManager::new(3);

        for i in 0..5 {
            manager.notify(Notification::system(
                format!("Notif {}", i),
                "body",
            ));
        }

        assert!(manager.all().len() <= 3);
    }

    #[test]
    fn test_by_category() {
        let manager = NotificationManager::new(100);
        manager.notify(Notification::system("Sys", "body"));
        manager.notify(Notification::ai("AI", "body"));
        manager.notify(Notification::system("Sys2", "body"));

        let system_notifs = manager.by_category(NotificationCategory::System);
        assert_eq!(system_notifs.len(), 2);

        let ai_notifs = manager.by_category(NotificationCategory::Ai);
        assert_eq!(ai_notifs.len(), 1);
    }

    #[test]
    fn test_filter() {
        let manager = NotificationManager::new(100);
        manager.notify(Notification::system("Sys", "body"));
        manager.notify(Notification::ai("AI", "body"));

        let filter = NotificationFilter::unread();
        let results = manager.filter(&filter);
        assert_eq!(results.len(), 2);
    }

    #[test]
    fn test_check_expirations() {
        let manager = NotificationManager::new(100);
        let expired = Notification::system("Old", "body")
            .expires_at(chrono::Utc::now() - chrono::Duration::hours(1));
        manager.schedule_notification(expired);

        let removed = manager.check_expirations();
        assert_eq!(removed, 1);
    }
}

