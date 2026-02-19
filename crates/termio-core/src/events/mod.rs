//! Event system
//!
//! Pub/sub event bus for component communication.

mod bus;
mod types;

pub use bus::EventBus;
pub use types::{Event, EventPayload, SyncEvent, SystemEvent};
