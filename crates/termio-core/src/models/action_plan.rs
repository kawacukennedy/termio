//! Action plan model for autonomous task execution
//!
//! Represents multi-step plans the AI creates and executes (FA-002).
//!
//! ## Overview
//!
//! Action plans enable TERMIO to autonomously execute complex tasks:
//! - Breaking down user requests into steps
//! - Executing each step with appropriate tools
//! - Handling failures and retries
//! - Requiring approval for sensitive actions
//!
//! ## Status Lifecycle
//!
//! ```text
//! Pending → RequiresApproval → InProgress → Completed
//!                      ↓
//!                   Failed
//! ```
//!
//! ## Action Types
//!
//! | Type | Description | Example |
//! |------|-------------|--------|
//! | app_intent | Execute app-specific actions | "Send email", "Create calendar event" |
//! | computer_vision | Image/analysis tasks | "Analyze screenshot", "OCR" |
//! | shell_command | Run terminal commands | "git push", "npm install" |
//! | http_request | API calls | "Fetch weather", "Post to webhook" |
//!
//! ## Approval Flow
//!
//! 1. AI creates plan with steps
//! 2. If `requires_approval = true`, status becomes `RequiresApproval`
//! 3. User reviews and approves/denies
//! 4. On approval, execution begins
//! 5. Each step runs sequentially, tracking results
//! 6. Plan completes or fails based on step outcomes

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum PlanStatus {
    Pending,
    InProgress,
    Completed,
    Failed,
    RequiresApproval,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ActionType {
    AppIntent,
    ComputerVision,
    ShellCommand,
    HttpRequest,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActionStep {
    pub step_id: u32,
    pub description: String,
    pub action_type: ActionType,
    pub target: String,
    pub parameters: serde_json::Value,
    pub status: PlanStatus,
    pub result: Option<serde_json::Value>,
}

impl ActionStep {
    pub fn new(
        step_id: u32,
        description: impl Into<String>,
        action_type: ActionType,
        target: impl Into<String>,
    ) -> Self {
        Self {
            step_id,
            description: description.into(),
            action_type,
            target: target.into(),
            parameters: serde_json::Value::Object(serde_json::Map::new()),
            status: PlanStatus::Pending,
            result: None,
        }
    }

    pub fn complete(&mut self, result: serde_json::Value) {
        self.status = PlanStatus::Completed;
        self.result = Some(result);
    }

    pub fn fail(&mut self, error: impl Into<String>) {
        self.status = PlanStatus::Failed;
        self.result = Some(serde_json::json!({ "error": error.into() }));
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActionPlan {
    pub id: Uuid,
    pub user_id: Uuid,
    pub trigger: String,
    pub status: PlanStatus,
    pub steps: Vec<ActionStep>,
    pub created_at: DateTime<Utc>,
    pub completed_at: Option<DateTime<Utc>>,
    pub requires_approval: bool,
    pub approval_granted: bool,
}

impl ActionPlan {
    pub fn new(user_id: Uuid, trigger: impl Into<String>) -> Self {
        Self {
            id: Uuid::new_v4(),
            user_id,
            trigger: trigger.into(),
            status: PlanStatus::Pending,
            steps: Vec::new(),
            created_at: Utc::now(),
            completed_at: None,
            requires_approval: false,
            approval_granted: false,
        }
    }

    pub fn add_step(&mut self, step: ActionStep) {
        self.steps.push(step);
    }

    pub fn require_approval(&mut self) {
        self.requires_approval = true;
        self.status = PlanStatus::RequiresApproval;
    }

    pub fn approve(&mut self) {
        self.approval_granted = true;
        self.status = PlanStatus::InProgress;
    }

    pub fn next_pending_step(&self) -> Option<usize> {
        self.steps.iter().position(|s| s.status == PlanStatus::Pending)
    }

    pub fn is_complete(&self) -> bool {
        self.steps.iter().all(|s| s.status == PlanStatus::Completed)
    }

    pub fn complete(&mut self) {
        self.status = PlanStatus::Completed;
        self.completed_at = Some(Utc::now());
    }

    pub fn fail(&mut self) {
        self.status = PlanStatus::Failed;
        self.completed_at = Some(Utc::now());
    }

    pub fn progress(&self) -> (usize, usize) {
        let completed = self.steps.iter().filter(|s| s.status == PlanStatus::Completed).count();
        (completed, self.steps.len())
    }
}
