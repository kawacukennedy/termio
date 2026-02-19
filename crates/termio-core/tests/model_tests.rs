//! Model Unit Tests
//!
//! Tests for core data models.

use uuid::Uuid;
use termio_core::models::*;

/// Test HealthData model creation
#[test]
fn test_health_data_creation() {
    let user_id = Uuid::new_v4();
    let hd = HealthData::new(
        user_id,
        HealthDataSource::Wearable,
        HealthDataType::HeartRate,
        72.0,
        "bpm",
    );

    assert_eq!(hd.user_id, user_id);
    assert_eq!(hd.value, 72.0);
    assert_eq!(hd.unit, "bpm");
    assert_eq!(hd.confidence, 1.0);
}

/// Test ActionPlan model creation
#[test]
fn test_action_plan_creation() {
    let user_id = Uuid::new_v4();
    let plan = ActionPlan::new(user_id, "Schedule a meeting");
    assert_eq!(plan.user_id, user_id);
    assert_eq!(plan.trigger, "Schedule a meeting");
    assert_eq!(plan.status, PlanStatus::Pending);
    assert!(plan.steps.is_empty());
    assert!(!plan.requires_approval);
}

/// Test ActionPlan with approval flow
#[test]
fn test_action_plan_approval() {
    let user_id = Uuid::new_v4();
    let mut plan = ActionPlan::new(user_id, "Delete files");
    plan.requires_approval = true;

    assert!(!plan.approval_granted);
    plan.approve();
    assert!(plan.approval_granted);
    assert_eq!(plan.status, PlanStatus::InProgress);
}

/// Test VectorClock operations
#[test]
fn test_vector_clock_operations() {
    use termio_core::sync::VectorClock;

    let mut vc1 = VectorClock::new();
    let mut vc2 = VectorClock::new();

    vc1.increment("device-A");
    vc2.increment("device-B");

    // Concurrent
    assert!(vc1.is_concurrent(&vc2));
    assert!(!vc1.dominates(&vc2));

    // Merge
    vc1.merge(&vc2);
    assert!(vc1.dominates(&vc2));

    // Get
    assert_eq!(vc1.get("device-A"), 1);
    assert_eq!(vc1.get("device-B"), 1);
    assert_eq!(vc1.get("unknown"), 0);
}

/// Test CrdtRegister convergence
#[test]
fn test_crdt_register_convergence() {
    use termio_core::sync::CrdtRegister;

    let mut reg_a = CrdtRegister::new("initial".to_string(), "A");
    let mut reg_b = CrdtRegister::new("initial".to_string(), "B");

    // Concurrent edits
    reg_a.set("value_a".to_string());
    reg_b.set("value_b".to_string());

    // Merge in both directions
    reg_a.merge(&reg_b);
    reg_b.merge(&reg_a);

    // Should converge to same value
    assert_eq!(reg_a.value, reg_b.value);
}

/// Test Notification with filter
#[test]
fn test_notification_filter() {
    use termio_core::notifications::*;

    let notif = Notification::system("Test", "body");
    let filter = NotificationFilter::unread();
    assert!(notif.matches_filter(&filter));

    let mut read_notif = Notification::system("Test2", "body");
    read_notif.mark_read();
    assert!(!read_notif.matches_filter(&filter));
}

/// Test Conversation model
#[test]
fn test_conversation_creation() {
    let conv = Conversation::new(Uuid::new_v4(), Uuid::new_v4());
    assert!(conv.messages.is_empty());
}

/// Test Message model
#[test]
fn test_message_creation() {
    let msg = Message::user("Hello, TERMIO!");
    assert_eq!(msg.content, "Hello, TERMIO!");

    let assistant_msg = Message::assistant("Hello! How can I help?");
    assert_eq!(assistant_msg.content, "Hello! How can I help?");
}
