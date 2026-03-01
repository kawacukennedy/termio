//! Event bus
//!
//! Asynchronous event bus using Tokio broadcast channels.
//!
//! ## Overview
//!
//! The event bus enables loose coupling between TERMIO components:
//! - Subsystems publish events without knowing subscribers
//! - Multiple subscribers can receive same event
//! - Events are async and non-blocking
//!
//! ## Usage
//!
//! ```rust
//! // Create bus
//! let bus = EventBus::new(1024);
//!
//! // Subscribe
//! let mut rx = bus.subscribe();
//!
//! // Publish
//! bus.publish(Event { ... })?;
//!
//! // Receive
//! while let Some(event) = rx.recv().await { ... }
//! ```
//!
//! ## Event Flow
//!
//! ```text
//! [Component A] --publish--> [Event Bus] --broadcast--> [Component B]
//!                                                         [Component C]
//! ```

use tokio::sync::broadcast;
use std::sync::Arc;

use crate::error::Result;
use super::types::Event;

/// Event bus for system-wide communication
#[derive(Clone)]
pub struct EventBus {
    sender: broadcast::Sender<Event>,
}

impl EventBus {
    /// Create a new event bus with capacity
    pub fn new(capacity: usize) -> Self {
        let (sender, _) = broadcast::channel(capacity);
        Self { sender }
    }

    /// Publish an event
    pub fn publish(&self, event: Event) -> Result<usize> {
        self.sender
            .send(event)
            .map_err(|e| crate::error::Error::System(format!("Failed to publish event: {}", e)))
    }

    /// Subscribe to events
    pub fn subscribe(&self) -> broadcast::Receiver<Event> {
        self.sender.subscribe()
    }
}

impl Default for EventBus {
    fn default() -> Self {
        Self::new(1024)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::events::types::{SystemEvent, EventPayload};
    use uuid::Uuid;
    use chrono::Utc;

    #[tokio::test]
    async fn test_pub_sub() {
        let bus = EventBus::new(16);
        let mut rx1 = bus.subscribe();
        let mut rx2 = bus.subscribe();

        let event = Event {
            id: Uuid::new_v4(),
            timestamp: Utc::now(),
            payload: EventPayload::System(SystemEvent::Startup),
            source: "test".to_string(),
        };

        bus.publish(event.clone()).unwrap();

        let recv1 = rx1.recv().await.unwrap();
        let recv2 = rx2.recv().await.unwrap();

        assert_eq!(recv1.id, event.id);
        assert_eq!(recv2.id, event.id);
    }
}
