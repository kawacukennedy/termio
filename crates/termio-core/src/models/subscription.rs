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
