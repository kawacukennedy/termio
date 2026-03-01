//! Subscription and billing model
//!
//! Manages user subscription tiers, payment methods, and feature access.
//!
//! ## Subscription Tiers
//!
//! | Tier | Price | Features |
//! |------|-------|----------|
//! | freemium | $0 | Basic AI, 50 messages/day, local-only |
//! | pro | $19/mo | Unlimited messages, cloud sync, voice input |
//! | business | $49/mo/user | Team sharing, API access, priority support |
//! | enterprise | Custom | On-premise deployment, SSO, SLA |
//!
//! ## Feature Flags
//!
//! Each tier includes specific features stored in the `features` JSON field:
//! - `voice_input`: Enable voice commands
//! - `cloud_sync`: Cross-device synchronization
//! - `plugins`: Load custom WASM plugins
//! - `smart_home`: IoT device integration
//! - `health_integration`: Wearable data sync
//! - `api_access`: REST API access
//!
//! ## Payment Providers
//!
//! - **Stripe**: Credit cards, Apple Pay, Google Pay
//! - **Binance**: Cryptocurrency payments (USDT)
//! - **Manual**: Enterprise billing with invoice

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum SubscriptionTier {
    Freemium,
    Pro,
    Business,
    Enterprise,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum SubscriptionStatus {
    Active,
    PastDue,
    Canceled,
    Expired,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum PaymentProvider {
    Stripe,
    Binance,
    Manual,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Subscription {
    pub id: Uuid,
    pub user_id: Uuid,
    pub tier: SubscriptionTier,
    pub status: SubscriptionStatus,
    pub provider: PaymentProvider,
    pub provider_subscription_id: Option<String>,
    pub start_date: DateTime<Utc>,
    pub end_date: DateTime<Utc>,
    pub auto_renew: bool,
    pub features: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum PaymentMethodType {
    Card,
    BankAccount,
    Crypto,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PaymentMethod {
    pub id: Uuid,
    pub user_id: Uuid,
    pub method_type: PaymentMethodType,
    pub details_encrypted: String, 
    pub is_default: bool,
}
