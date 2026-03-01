//! Event system
//!
//! Pub/sub event bus for component communication.
//!
//! # Overview
//!
//! The event system allows loose coupling between TERMIO components.
//! Components publish events without knowing who's listening,
//! and subscribe to events without knowing who's publishing.
//!
//! # Event Types
//!
//! - **System**: Startup, shutdown, errors, config changes
//! - **Conversation**: Created, messages, updates
//! - **AI**: Request started, token generated, completed, errors
//! - **Memory**: Entry created, updated, searches
//! - **Sync**: Peer connected/disconnected, sync started/completed, conflicts
//!
//! # Usage
//!
//! ```rust
//! use termio_core::events::{EventBus, Event, EventPayload, SystemEvent};
//!
//! let bus = EventBus::new(1024);
//!
//! // Subscribe
//! let mut rx = bus.subscribe();
//!
//! // Publish
//! bus.publish(Event::new(
//!     EventPayload::System(SystemEvent::Startup),
//!     "main"
//! )).unwrap();
//! ```

mod bus;
mod types;

pub use bus::EventBus;
pub use types::{Event, EventPayload, SyncEvent, SystemEvent};
