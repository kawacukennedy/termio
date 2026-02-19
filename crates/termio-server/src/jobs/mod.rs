pub mod memory_indexing;
pub mod proactive_suggestions;
pub mod notification_cleanup;
pub mod sync_polling;
pub mod knowledge_inference;
pub mod encrypted_backup;
pub mod model_optimization;

use std::time::Duration;
use tokio::sync::watch;

/// Background job scheduler
///
/// Manages periodic tasks with graceful shutdown support.
pub struct JobScheduler {
    shutdown_tx: watch::Sender<bool>,
    shutdown_rx: watch::Receiver<bool>,
}

impl JobScheduler {
    /// Create a new job scheduler
    pub fn new() -> Self {
        let (shutdown_tx, shutdown_rx) = watch::channel(false);
        Self {
            shutdown_tx,
            shutdown_rx,
        }
    }

    /// Start all background jobs
    ///
    /// Spawns periodic tasks that run until shutdown is signalled.
    pub fn start(&self, state: crate::state::AppState) {
        // Memory indexing — every 6 hours
        let rx1 = self.shutdown_rx.clone();
        let state1 = state.clone();
        tokio::spawn(async move {
            Self::run_periodic(
                "memory_indexing",
                Duration::from_secs(6 * 60 * 60),
                rx1,
                move || {
                    let s = state1.clone();
                    async move {
                        memory_indexing::run(&s).await;
                    }
                },
            )
            .await;
        });

        // Sync polling — every 5 minutes
        let rx2 = self.shutdown_rx.clone();
        let state2 = state.clone();
        tokio::spawn(async move {
            Self::run_periodic(
                "sync_polling",
                Duration::from_secs(5 * 60),
                rx2,
                move || {
                    let s = state2.clone();
                    async move {
                        sync_polling::run(&s).await;
                    }
                },
            )
            .await;
        });

        // Notification cleanup — every 15 minutes
        let rx3 = self.shutdown_rx.clone();
        let state3 = state.clone();
        tokio::spawn(async move {
            Self::run_periodic(
                "notification_cleanup",
                Duration::from_secs(15 * 60),
                rx3,
                move || {
                    let s = state3.clone();
                    async move {
                        notification_cleanup::run(&s).await;
                    }
                },
            )
            .await;
        });

        // Knowledge inference — every 24 hours (spec: daily at 4 AM)
        let rx4 = self.shutdown_rx.clone();
        let state4 = state.clone();
        tokio::spawn(async move {
            Self::run_periodic(
                "knowledge_inference",
                Duration::from_secs(24 * 60 * 60),
                rx4,
                move || {
                    let s = state4.clone();
                    async move {
                        knowledge_inference::run(&s).await;
                    }
                },
            )
            .await;
        });

        // Encrypted backup — every 24 hours (spec: daily at 2 AM)
        let rx5 = self.shutdown_rx.clone();
        let state5 = state.clone();
        tokio::spawn(async move {
            Self::run_periodic(
                "encrypted_backup",
                Duration::from_secs(24 * 60 * 60),
                rx5,
                move || {
                    let s = state5.clone();
                    async move {
                        encrypted_backup::run(&s).await;
                    }
                },
            )
            .await;
        });

        // Model optimization — every 2 hours (spec: on idle)
        let rx6 = self.shutdown_rx.clone();
        let state6 = state.clone();
        tokio::spawn(async move {
            Self::run_periodic(
                "model_optimization",
                Duration::from_secs(2 * 60 * 60),
                rx6,
                move || {
                    let s = state6.clone();
                    async move {
                        model_optimization::run(&s).await;
                    }
                },
            )
            .await;
        });

        // Proactive suggestions — every 2 hours
        let rx7 = self.shutdown_rx.clone();
        let state7 = state.clone();
        tokio::spawn(async move {
            Self::run_periodic(
                "proactive_suggestions",
                Duration::from_secs(2 * 60 * 60),
                rx7,
                move || {
                    let s = state7.clone();
                    async move {
                        proactive_suggestions::run(&s).await;
                    }
                },
            )
            .await;
        });

        tracing::info!("Background job scheduler started (7 jobs)");
    }

    /// Run a periodic task with shutdown support
    async fn run_periodic<F, Fut>(
        name: &str,
        interval: Duration,
        mut shutdown_rx: watch::Receiver<bool>,
        task_fn: F,
    ) where
        F: Fn() -> Fut,
        Fut: std::future::Future<Output = ()>,
    {
        let mut ticker = tokio::time::interval(interval);
        // Skip the first immediate tick
        ticker.tick().await;

        loop {
            tokio::select! {
                _ = ticker.tick() => {
                    tracing::debug!("Running background job: {}", name);
                    task_fn().await;
                }
                _ = shutdown_rx.changed() => {
                    tracing::info!("Shutting down background job: {}", name);
                    break;
                }
            }
        }
    }

    /// Signal all background jobs to stop
    pub fn shutdown(&self) {
        let _ = self.shutdown_tx.send(true);
        tracing::info!("Background job scheduler shutdown signal sent");
    }
}

impl Default for JobScheduler {
    fn default() -> Self {
        Self::new()
    }
}
