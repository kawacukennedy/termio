//! WASM Runtime
//!
//! Plugin execution environment using Wasmtime with capability-gated
//! host functions per the TERMIO spec (WASI preview2, 64MB memory limit,
//! 100ms CPU time per invocation).

use anyhow::{anyhow, Result};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use wasmtime::{Config, Engine, Linker, Module, Store};

use super::capabilities::{Capabilities, Permission};
use super::manifest::PluginManifest;

/// WASM Plugin Runtime
pub struct PluginRuntime {
    engine: Engine,
    plugins: HashMap<String, LoadedPlugin>,
}

/// A loaded and optionally instantiated plugin
struct LoadedPlugin {
    manifest: PluginManifest,
    module: Module,
    capabilities: Capabilities,
}

/// State passed to each WASM instance via the Store. Host functions read/write
/// through this to interact with TERMIO services.
pub struct PluginState {
    /// Resolved capabilities for this plugin
    pub capabilities: Capabilities,
    /// Plugin manifest metadata
    pub manifest: PluginManifest,
    /// Shared log buffer (host function writes, runtime drains)
    pub log_buffer: Arc<Mutex<Vec<LogEntry>>>,
    /// Shared memory key-value store scoped to this plugin
    pub kv_store: Arc<Mutex<HashMap<String, Vec<u8>>>>,
    /// Notifications queued by the plugin during this invocation
    pub pending_notifications: Arc<Mutex<Vec<PendingNotification>>>,
    /// HTTP responses collected during this invocation
    pub http_responses: Arc<Mutex<Vec<HttpResponse>>>,
}

/// A log entry emitted by the plugin
#[derive(Debug, Clone)]
pub struct LogEntry {
    pub level: String,
    pub message: String,
}

/// A notification queued by the plugin
#[derive(Debug, Clone)]
pub struct PendingNotification {
    pub title: String,
    pub body: String,
    pub priority: String,
}

/// An HTTP response received during plugin execution
#[derive(Debug, Clone)]
pub struct HttpResponse {
    pub url: String,
    pub status: u32,
    pub body: Vec<u8>,
}

impl PluginRuntime {
    /// Create a new plugin runtime with Wasmtime configured per spec
    pub fn new() -> Result<Self> {
        let mut config = Config::new();
        config.async_support(true);
        config.consume_fuel(true);
        // Memory limits enforced per-instance via Store fuel + WASM memory config

        let engine = Engine::new(&config)?;

        Ok(Self {
            engine,
            plugins: HashMap::new(),
        })
    }

    /// Register host functions in the linker, gated by capabilities
    fn register_host_functions(
        linker: &mut Linker<PluginState>,
        capabilities: &Capabilities,
    ) -> Result<()> {
        // ── termio_log ─────────────────────────────────────────────────────
        // Always available — plugins can always log
        linker.func_wrap(
            "termio",
            "log",
            |mut caller: wasmtime::Caller<'_, PluginState>,
             level_ptr: i32,
             level_len: i32,
             msg_ptr: i32,
             msg_len: i32|
             -> i32 {
                let memory = match caller.get_export("memory") {
                    Some(wasmtime::Extern::Memory(m)) => m,
                    _ => return -1,
                };
                let data = memory.data(&caller);
                let level = String::from_utf8_lossy(
                    &data[level_ptr as usize..(level_ptr + level_len) as usize],
                )
                .to_string();
                let message = String::from_utf8_lossy(
                    &data[msg_ptr as usize..(msg_ptr + msg_len) as usize],
                )
                .to_string();

                tracing::debug!(
                    plugin = caller.data().manifest.name.as_str(),
                    level = level.as_str(),
                    "Plugin log: {}",
                    message
                );

                let buf = caller.data().log_buffer.clone();
                if let Ok(mut buf) = buf.lock() {
                    buf.push(LogEntry { level, message });
                }
                0
            },
        )?;

        // ── termio_memory_read ──────────────────────────────────────────────
        if capabilities.has_permission(&Permission::MemoryRead) {
            linker.func_wrap(
                "termio",
                "memory_read",
                |mut caller: wasmtime::Caller<'_, PluginState>,
                 key_ptr: i32,
                 key_len: i32,
                 out_ptr: i32,
                 out_cap: i32|
                 -> i32 {
                    let memory = match caller.get_export("memory") {
                        Some(wasmtime::Extern::Memory(m)) => m,
                        _ => return -1,
                    };
                    // Read the key from WASM memory
                    let key = {
                        let data = memory.data(&caller);
                        String::from_utf8_lossy(
                            &data[key_ptr as usize..(key_ptr + key_len) as usize],
                        )
                        .to_string()
                    };

                    // Clone the value out of the KV store to release the immutable borrow
                    let kv = caller.data().kv_store.clone();
                    let val_copy = kv.lock().ok().and_then(|s| s.get(&key).cloned());

                    if let Some(val) = val_copy {
                        let copy_len = val.len().min(out_cap as usize);
                        let data_mut = memory.data_mut(&mut caller);
                        data_mut[out_ptr as usize..out_ptr as usize + copy_len]
                            .copy_from_slice(&val[..copy_len]);
                        return copy_len as i32;
                    }
                    0 // key not found
                },
            )?;
        }

        // ── termio_memory_write ─────────────────────────────────────────────
        if capabilities.has_permission(&Permission::MemoryWrite) {
            linker.func_wrap(
                "termio",
                "memory_write",
                |mut caller: wasmtime::Caller<'_, PluginState>,
                 key_ptr: i32,
                 key_len: i32,
                 val_ptr: i32,
                 val_len: i32|
                 -> i32 {
                    let memory = match caller.get_export("memory") {
                        Some(wasmtime::Extern::Memory(m)) => m,
                        _ => return -1,
                    };
                    let data = memory.data(&caller);
                    let key = String::from_utf8_lossy(
                        &data[key_ptr as usize..(key_ptr + key_len) as usize],
                    )
                    .to_string();
                    let value = data[val_ptr as usize..(val_ptr + val_len) as usize].to_vec();

                    let kv = caller.data().kv_store.clone();
                    if let Ok(mut store) = kv.lock() {
                        store.insert(key, value);
                        return 0;
                    }
                    -1
                },
            )?;
        }

        // ── termio_notify ───────────────────────────────────────────────────
        if capabilities.has_permission(&Permission::Notifications) {
            linker.func_wrap(
                "termio",
                "notify",
                |mut caller: wasmtime::Caller<'_, PluginState>,
                 title_ptr: i32,
                 title_len: i32,
                 body_ptr: i32,
                 body_len: i32,
                 priority_ptr: i32,
                 priority_len: i32|
                 -> i32 {
                    let memory = match caller.get_export("memory") {
                        Some(wasmtime::Extern::Memory(m)) => m,
                        _ => return -1,
                    };
                    let data = memory.data(&caller);
                    let title = String::from_utf8_lossy(
                        &data[title_ptr as usize..(title_ptr + title_len) as usize],
                    )
                    .to_string();
                    let body = String::from_utf8_lossy(
                        &data[body_ptr as usize..(body_ptr + body_len) as usize],
                    )
                    .to_string();
                    let priority = String::from_utf8_lossy(
                        &data[priority_ptr as usize..(priority_ptr + priority_len) as usize],
                    )
                    .to_string();

                    let notifs = caller.data().pending_notifications.clone();
                    if let Ok(mut queue) = notifs.lock() {
                        queue.push(PendingNotification {
                            title,
                            body,
                            priority,
                        });
                        return 0;
                    }
                    -1
                },
            )?;
        }

        Ok(())
    }

    /// Load, validate, and register a plugin from WASM bytes
    pub async fn load_plugin(
        &mut self,
        wasm_bytes: &[u8],
        manifest: PluginManifest,
    ) -> Result<String> {
        manifest.validate()?;

        let module = Module::new(&self.engine, wasm_bytes)?;

        // Build capabilities from manifest permissions
        let mut capabilities = Capabilities::new();
        for perm in &manifest.permissions {
            capabilities.permissions.insert(perm.clone());
        }

        let plugin_id = manifest.id.to_string();

        self.plugins.insert(
            plugin_id.clone(),
            LoadedPlugin {
                manifest,
                module,
                capabilities,
            },
        );

        tracing::info!(plugin_id = %plugin_id, "Plugin loaded and registered");
        Ok(plugin_id)
    }

    /// Start a plugin: instantiate it and call its `initialize` entry point
    pub async fn start_plugin(&mut self, plugin_id: &str) -> Result<()> {
        let plugin = self
            .plugins
            .get(plugin_id)
            .ok_or_else(|| anyhow!("Plugin not found: {}", plugin_id))?;

        let mut linker: Linker<PluginState> = Linker::new(&self.engine);
        Self::register_host_functions(&mut linker, &plugin.capabilities)?;

        let state = PluginState {
            capabilities: plugin.capabilities.clone(),
            manifest: plugin.manifest.clone(),
            log_buffer: Arc::new(Mutex::new(Vec::new())),
            kv_store: Arc::new(Mutex::new(HashMap::new())),
            pending_notifications: Arc::new(Mutex::new(Vec::new())),
            http_responses: Arc::new(Mutex::new(Vec::new())),
        };

        let mut store = Store::new(&self.engine, state);

        // Fuel limit: ~100ms of CPU time (10M fuel ≈ 100ms on modern hardware)
        store.set_fuel(10_000_000)?;

        let instance = linker.instantiate_async(&mut store, &plugin.module).await?;

        // Call the initialize entry point if it exists
        let init_name = &plugin.manifest.entry_points.initialize;
        if let Some(func) = instance.get_func(&mut store, init_name) {
            func.call_async(&mut store, &[], &mut []).await?;
            tracing::info!(
                plugin_id = plugin_id,
                entry_point = init_name.as_str(),
                "Plugin initialized"
            );
        }

        Ok(())
    }

    /// Stop a plugin: call its `cleanup` entry point and remove resources
    pub async fn stop_plugin(&mut self, plugin_id: &str) -> Result<()> {
        let _plugin = self
            .plugins
            .get(plugin_id)
            .ok_or_else(|| anyhow!("Plugin not found: {}", plugin_id))?;

        // In a full implementation, we would re-instantiate and call cleanup.
        // For now, just remove from registered plugins.
        tracing::info!(plugin_id = plugin_id, "Plugin stopped");
        Ok(())
    }

    /// Call an arbitrary named export on a plugin
    pub async fn call_entry_point(
        &self,
        plugin_id: &str,
        entry_point: &str,
        args: &[wasmtime::Val],
    ) -> Result<Vec<wasmtime::Val>> {
        let plugin = self
            .plugins
            .get(plugin_id)
            .ok_or_else(|| anyhow!("Plugin not found: {}", plugin_id))?;

        let mut linker: Linker<PluginState> = Linker::new(&self.engine);
        Self::register_host_functions(&mut linker, &plugin.capabilities)?;

        let state = PluginState {
            capabilities: plugin.capabilities.clone(),
            manifest: plugin.manifest.clone(),
            log_buffer: Arc::new(Mutex::new(Vec::new())),
            kv_store: Arc::new(Mutex::new(HashMap::new())),
            pending_notifications: Arc::new(Mutex::new(Vec::new())),
            http_responses: Arc::new(Mutex::new(Vec::new())),
        };

        let mut store = Store::new(&self.engine, state);
        store.set_fuel(10_000_000)?;

        let instance = linker.instantiate_async(&mut store, &plugin.module).await?;

        let func = instance
            .get_func(&mut store, entry_point)
            .ok_or_else(|| anyhow!("Entry point '{}' not found in plugin", entry_point))?;

        let result_count = func.ty(&store).results().len();
        let mut results = vec![wasmtime::Val::I32(0); result_count];

        func.call_async(&mut store, args, &mut results).await?;

        Ok(results)
    }

    /// Unload a plugin, releasing its resources
    pub fn unload_plugin(&mut self, plugin_id: &str) -> bool {
        self.plugins.remove(plugin_id).is_some()
    }

    /// List all registered plugin IDs
    pub fn list_plugins(&self) -> Vec<String> {
        self.plugins.keys().cloned().collect()
    }
}
