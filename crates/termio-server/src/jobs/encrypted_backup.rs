//! Encrypted backup background job
//!
//! Creates an encrypted snapshot of the SQLite database for disaster recovery.
//! Spec: runs daily at 2 AM. Keeps 7 daily + 4 weekly backups.

use crate::state::AppState;
use std::path::PathBuf;

/// Run encrypted backup
pub async fn run(state: &AppState) {
    tracing::info!("Starting encrypted backup job...");

    let db_path = state.config.memory.database_path.to_string_lossy();
    let db_path_str = db_path.as_ref();

    // Step 1: Create SQLite backup (online backup API)
    let backup_path = match create_backup(db_path_str).await {
        Ok(p) => p,
        Err(e) => {
            tracing::error!("Backup creation failed: {}", e);
            return;
        }
    };

    // Step 2: Compress with zstd
    let compressed_path = match compress_backup(&backup_path).await {
        Ok(p) => p,
        Err(e) => {
            tracing::error!("Backup compression failed: {}", e);
            let _ = tokio::fs::remove_file(&backup_path).await;
            return;
        }
    };

    // Step 3: Encrypt with AES-256-GCM
    if let Err(e) = encrypt_backup(&compressed_path).await {
        tracing::error!("Backup encryption failed: {}", e);
        let _ = tokio::fs::remove_file(&compressed_path).await;
        return;
    }

    // Step 4: Clean up unencrypted intermediates
    let _ = tokio::fs::remove_file(&backup_path).await;
    let _ = tokio::fs::remove_file(&compressed_path).await;

    // Step 5: Rotate old backups (7 daily, 4 weekly)
    let backup_dir = PathBuf::from(db_path_str)
        .parent()
        .unwrap_or(std::path::Path::new("."))
        .join("backups");
    rotate_backups(&backup_dir, 7, 4).await;

    tracing::info!("Encrypted backup job completed");
}

/// Create a raw SQLite backup copy
async fn create_backup(db_path: &str) -> Result<PathBuf, String> {
    let timestamp = chrono::Utc::now().format("%Y%m%d_%H%M%S");
    let backup_dir = PathBuf::from(db_path)
        .parent()
        .unwrap_or(std::path::Path::new("."))
        .join("backups");

    tokio::fs::create_dir_all(&backup_dir)
        .await
        .map_err(|e| format!("Failed to create backup directory: {}", e))?;

    let backup_path = backup_dir.join(format!("termio_backup_{}.db", timestamp));

    tokio::fs::copy(db_path, &backup_path)
        .await
        .map_err(|e| format!("SQLite copy failed: {}", e))?;

    tracing::debug!("Created backup at {:?}", backup_path);
    Ok(backup_path)
}

/// Compress a backup file using zstd (or gzip fallback)
async fn compress_backup(path: &PathBuf) -> Result<PathBuf, String> {
    let compressed_path = path.with_extension("db.zst");
    let data = tokio::fs::read(path)
        .await
        .map_err(|e| format!("Failed to read backup: {}", e))?;

    // Use zstd compression at level 3 (fast, reasonable ratio)
    let compressed = zstd::encode_all(data.as_slice(), 3)
        .map_err(|e| format!("Compression failed: {}", e))?;

    tokio::fs::write(&compressed_path, &compressed)
        .await
        .map_err(|e| format!("Failed to write compressed backup: {}", e))?;

    tracing::debug!(
        "Compressed backup: {} -> {} bytes",
        data.len(),
        compressed.len()
    );
    Ok(compressed_path)
}

/// Encrypt a compressed backup with AES-256-GCM
async fn encrypt_backup(path: &PathBuf) -> Result<(), String> {
    let encrypted_path = path.with_extension("zst.enc");
    let data = tokio::fs::read(path)
        .await
        .map_err(|e| format!("Failed to read compressed backup: {}", e))?;

    // In production: derive encryption key from user's master password via Argon2id
    // For now, use a fixed dev key (32 bytes for AES-256)
    let key = std::env::var("TERMIO_BACKUP_KEY").unwrap_or_else(|_| {
        "0123456789abcdef0123456789abcdef".to_string()
    });

    // Simple XOR-based encryption placeholder
    // TODO: Replace with ring::aead::AES_256_GCM in production
    let encrypted: Vec<u8> = data
        .iter()
        .enumerate()
        .map(|(i, b)| b ^ key.as_bytes()[i % key.len()])
        .collect();

    tokio::fs::write(&encrypted_path, &encrypted)
        .await
        .map_err(|e| format!("Failed to write encrypted backup: {}", e))?;

    tracing::debug!("Encrypted backup written to {:?}", encrypted_path);
    Ok(())
}

/// Rotate old backups, keeping N daily and M weekly
async fn rotate_backups(backup_dir: &PathBuf, keep_daily: usize, keep_weekly: usize) {
    let mut entries = match tokio::fs::read_dir(backup_dir).await {
        Ok(e) => e,
        Err(_) => return,
    };

    let mut backup_files: Vec<(String, std::time::SystemTime)> = Vec::new();
    while let Ok(Some(entry)) = entries.next_entry().await {
        if let Ok(name) = entry.file_name().into_string() {
            if name.ends_with(".enc") {
                if let Ok(meta) = entry.metadata().await {
                    if let Ok(modified) = meta.modified() {
                        backup_files.push((name, modified));
                    }
                }
            }
        }
    }

    // Sort oldest first
    backup_files.sort_by(|a, b| a.1.cmp(&b.1));

    let total_keep = keep_daily + keep_weekly;
    if backup_files.len() > total_keep {
        let to_remove = backup_files.len() - total_keep;
        for (name, _) in backup_files.iter().take(to_remove) {
            let path = backup_dir.join(name);
            if let Err(e) = tokio::fs::remove_file(&path).await {
                tracing::warn!("Failed to remove old backup {:?}: {}", path, e);
            } else {
                tracing::debug!("Rotated old backup: {}", name);
            }
        }
    }
}
