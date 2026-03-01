# TERMIO Documentation

## Project Overview

TERMIO is a next-generation agentic AI assistant that is terminal-native, offline-first, privacy-focused, and cross-platform. The project implements a comprehensive AI assistant with features including:

- Full-duplex conversational AI with ultra-low latency
- Autonomous multi-step task execution (Agentic OS)
- Long-term personal knowledge graph
- Visual intelligence with AR overlay
- Background reasoning for proactive suggestions
- Smart home control via Matter/Thread
- Personal health monitoring
- Hybrid AI inference (local + cloud)
- Three-tier memory architecture
- Plugin ecosystem with WASM sandbox
- Cross-device synchronization

## Architecture

```
TERMIO/
├── crates/
│   ├── termio-core/       # Core Rust library
│   ├── termio-server/     # HTTP API server
│   └── termio-tui/        # Terminal UI
├── apps/
│   ├── mobile/           # React Native mobile app
│   └── desktop/          # Desktop app (Tauri)
├── config/               # Configuration files
└── migrations/           # Database migrations
```

---

## termio-core

The core Rust library providing shared functionality for all TERMIO components.

### Modules

#### 1. Authentication (`src/auth/`)

##### Session Management (`session.rs`)

Implements JWT-based session tokens for API authentication.

- **SessionManager**: Creates and verifies JWT session tokens
- **Claims**: JWT payload containing user ID, device ID, expiration, and permissions/scopes
- **Session**: Active session with token, user ID, device ID, and expiration timestamp

```rust
// Example: Creating a session
let manager = SessionManager::new(secret.as_bytes());
let session = manager.create_session(
    user_id,
    device_id,
    Duration::hours(1),
    vec!["read".to_string()]
)?;
```

##### Device Keys (`device_key.rs`)

Ed25519 key pairs for device identification and signing.

- **DeviceKey**: Generates and manages Ed25519 key pairs for device identity
- **KeyPair**: Serializable format for storing keys (Base64 encoded)

#### 2. Cryptography (`src/crypto/`)

##### Encryption (`encryption.rs`)

AES-256-GCM authenticated encryption for data at rest.

- **EncryptedData**: Contains nonce and ciphertext with Base64 encoding support
- **encrypt()**: Encrypts plaintext with AES-256-GCM
- **decrypt()**: Decrypts encrypted data

##### Key Derivation (`key_derivation.rs`)

Argon2id password-based key derivation.

- **DerivedKey**: Contains 32-byte derived key and salt
- **derive_key()**: Creates a key from password using Argon2id (64MB memory, 3 iterations)
- **verify_password()**: Verifies password against stored key

#### 3. Data Models (`src/models/`)

##### Conversation (`conversation.rs`)

Multi-message conversation with context tracking.

- **Conversation**: Contains ID, user_id, device_id, session_id, messages, context_window, timestamps
- **ContextWindow**: Tracks token count, embeddings status, and summary
- Methods: `new()`, `add_message()`, `last_messages()`, `is_empty()`

##### Message (`message.rs`)

Individual message in a conversation.

- **Role**: `User`, `Assistant`, `System`
- **InputMode**: `Text`, `Voice`, `Screen`
- **MessageMetadata**: Stores input mode, confidence, model used, processing time
- **Message**: Builder pattern with `user()`, `assistant()`, `system()` constructors

##### Memory Entry (`memory_entry.rs`)

Semantic memory with embeddings for long-term storage.

- **MemorySource**: `Conversation`, `Document`, `Plugin`, `Manual`
- **SharingPolicy**: `Private`, `SharedDevices`, `SharedUsers`
- **MemoryMetadata**: Source, importance score (0-1), access frequency, tags
- **AccessControl**: Required capabilities, encryption key ID, sharing policy

##### Knowledge Graph (`knowledge_graph.rs`)

Graph-based knowledge representation with nodes and edges.

- **KnowledgeNode**: Entity with type, label, properties, optional embedding
- **KnowledgeEdge**: Relationships between nodes with weight (0-1)

##### Health Data (`health_data.rs`)

Biometric and health measurements from wearables.

- **HealthDataSource**: `Wearable`, `Manual`, `DeviceSensors`
- **HealthDataType**: `HeartRate`, `Hrv`, `Spo2`, `SkinTemperature`, `Steps`, `Sleep`, `Stress`

##### Action Plan (`action_plan.rs`)

Autonomous task execution plans.

- **PlanStatus**: `Pending`, `InProgress`, `Completed`, `Failed`, `RequiresApproval`
- **ActionType**: `AppIntent`, `ComputerVision`, `ShellCommand`, `HttpRequest`
- **ActionStep**: Individual step with description, target, parameters, status, result

##### Device Sync (`device_sync.rs`)

Cross-device synchronization state.

- **LastSync**: Timestamp, vector clock, hash
- **PendingChanges**: Count, size, oldest timestamp
- **SyncConfig**: auto_sync, wifi_only, battery_threshold, data_cap_mb

##### Subscription (`subscription.rs`)

Tier-based subscription management.

- **SubscriptionTier**: `Freemium`, `Pro`, `Business`, `Enterprise`
- **SubscriptionStatus**: `Active`, `PastDue`, `Canceled`, `Expired`
- **PaymentProvider**: `Stripe`, `Binance`, `Manual`

##### Smart Home (`smart_home.rs`)

Matter/Thread device control.

- **DeviceType**: `Light`, `Thermostat`, `Lock`, `Camera`, `Sensor`, `Speaker`
- **SmartDevice**: Device state and protocol (matter, thread)
- **HomeScene**: Automated scene with multiple actions

##### Document (`document.rs`)

Uploaded document processing.

- **DocumentStatus**: `Pending`, `Processing`, `Indexed`, `Failed`
- **DocumentType**: `Text`, `Markdown`, `Pdf`, `Code`, `Other`

#### 4. Memory System (`src/memory/`)

##### Ring Buffer (`ring_buffer.rs`)

Fast in-memory storage for recent context (last N items).

- **RingBuffer<T>**: Fixed-size buffer with O(1) insertion and access
- Methods: `push()`, `last()`, `first()`, `last_n()`, `len()`, `is_empty()`, `clear()`
- Default capacity: 100 (per spec)

##### Vector Store (`vector_store.rs`)

SQLite-backed vector storage for semantic search.

- **VectorEntry**: ID, content, embedding, metadata
- **cosine_similarity_impl()**: Computes cosine similarity between vectors
- Methods: `insert()`, `search()`, `delete()`, `get()`

##### Persistent Store (`store.rs`)

SQLite-backed storage for all data.

Tables created:
- `conversations` - Chat conversations
- `memory_entries` - Semantic memories
- `knowledge_nodes` - Graph nodes
- `knowledge_edges` - Graph edges
- `health_data` - Biometric data
- `action_plans` - Task plans
- `plugins` - Installed plugins
- `notifications` - User notifications
- `subscriptions` - Subscription info
- `payment_methods` - Payment methods
- `smart_devices` - Smart home devices
- `smart_scenes` - Smart home scenes

#### 5. Events (`src/events/`)

##### Event Bus (`bus.rs`)

Async pub/sub using Tokio broadcast channels.

- **EventBus**: Publish/subscribe event system
- Methods: `new()`, `publish()`, `subscribe()`

##### Event Types (`types.rs`)

Structured events for system communication.

- **Event**: ID, timestamp, payload, source
- **EventPayload**: System, Conversation, Ai, Memory, Sync variants
- **SystemEvent**: Startup, Shutdown, Error, ConfigReload
- **ConversationEvent**: Created, MessageReceived, MessageSent, Updated
- **AiEvent**: RequestStarted, TokenGenerated, ResponseCompleted, Error
- **MemoryEvent**: EntryCreated, EntryUpdated, SearchPerformed
- **SyncEvent**: Connected, Disconnected, SyncStarted, SyncCompleted, ConflictDetected

#### 6. Plugins (`src/plugins/`)

##### Manifest (`manifest.rs`)

Plugin metadata and configuration.

- **PluginManifest**: ID, name, version, description, author, permissions, entry_points, signature, compatibility
- **EntryPoints**: WASM module path, initialize, cleanup functions
- **PluginSignature**: Algorithm, value, timestamp
- **Compatibility**: Version range and platform support

##### Capabilities (`capabilities.rs`)

Capability-based security model.

- **Permission**: Network, Filesystem, AiCompute, MemoryRead, MemoryWrite, AudioRecord, Notifications
- **Capabilities**: Collection of granted permissions with `has_permission()`, `check_network()`, `check_fs()`

##### Runtime (`runtime.rs`)

WASM plugin execution using Wasmtime.

- **PluginRuntime**: Manages plugin loading and execution
- **PluginState**: Passed to WASM instances with capabilities, KV store, logs
- Host functions: `termio_log`, `termio_memory_read`, `termio_memory_write`, `termio_notify`
- Memory limit: 64MB, CPU time: 100ms per invocation

#### 7. Notifications (`src/notifications/`)

##### Types (`types.rs`)

Notification data structures.

- **NotificationPriority**: `Low`, `Medium`, `High`, `Critical`
- **NotificationType**: `Alert`, `Reminder`, `Suggestion`, `HealthAlert`, `System`
- **NotificationCategory**: `System`, `Ai`, `Sync`, `Plugin`, `Memory`, `User`, `Security`
- **NotificationStatus**: `Pending`, `Delivered`, `Read`, `Actioned`
- **QuietHours**: Configurable quiet hours with critical notification override
- **DeliveryChannel**: `Mobile`, `Desktop`, `Terminal`

##### Manager (`manager.rs`)

Notification lifecycle management.

- **NotificationManager**: Queue with max limit, quiet hours support
- Methods: `notify()`, `schedule_notification()`, `deliver_ready()`, `check_expirations()`, `unread()`, `mark_read()`, `dismiss()`, `filter()`

#### 8. Sync (`src/sync/`)

##### CRDT (`crdt.rs`)

Conflict-free replicated data types.

- **VectorClock**: Causality tracking with increment, merge, happens_before
- **CrdtRegister<T>**: Last-Writer-Wins register with automatic conflict resolution
- **ConflictResolution**: `LastWriterWins`, `KeepBoth`, `Custom`

##### Delta Sync (`delta.rs`)

Efficient state synchronization.

- **Delta**: Source node, version, operation, timestamp
- **Operation**: UpsertConversation, DeleteConversation, AddMessage, SetValue, DeleteRecord
- **SyncConflict**: Local and remote deltas with resolution
- **DeltaStore**: Change history with conflict detection

##### Peer (`peer.rs`)

P2P peer management.

- **PeerInfo**: ID, alias, discovered_at, last_seen, status, discovery_method
- **PeerStatus**: `Discovered`, `Connected`, `Idle`, `Unreachable`
- **DiscoveryMethod**: `Mdns`, `Manual`, `Relay`
- **PeerManager**: Local identity, known peers, mDNS discovery, relay fallback

#### 9. Voice (`src/voice/`)

##### Recorder (`recorder.rs`)

Cross-platform audio input using cpal.

- **AudioSample**: i16 format
- **AudioBuffer**: Samples, sample_rate, channels
- Methods: `duration_secs()`, `to_mono()`
- **RecordingState**: `Idle`, `Recording`, `Processing`

##### Recognizer (`recognizer.rs`)

Offline speech-to-text using Vosk.

- **RecognitionResult**: text, confidence, is_final
- **VoiceRecognizer**: Model loading and recognition
- Methods: `load_model()`, `recognize()`, `start_streaming()`

#### 10. Health (`src/health/`)

##### Monitor (`monitor.rs`)

System health checking.

- **HealthStatus**: `Healthy`, `Degraded`, `Unhealthy`
- **SystemResources**: Uptime, memory, database connection
- **ServiceHealth**: Service name, availability, response time
- **HealthMonitor**: Creates health reports combining all checks

#### 11. Configuration (`src/config.rs`)

Hierarchical config loading.

- **Config**: Main config with app, ai, memory, server, ui sections
- **AiConfig**: model_path, max_context_tokens, inference_timeout_ms, service_url, local_inference
- **MemoryConfig**: ring_buffer_size, database_path, query_timeout_ms, enable_embeddings
- **ServerConfig**: host, port, enable_cors
- **UiConfig**: theme, animations, shortcut_prefix

#### 12. Error Handling (`src/error.rs`)

Categorized error types.

Error codes:
- 4000-4099: User errors (InvalidInput, InsufficientPermissions, QuotaExceeded)
- 5000-5099: System errors (Database, Config, Io, Serialization, Auth, Encryption)
- 6000-6099: AI errors (ModelLoadFailed, InferenceTimeout, ContextOverflow)
- 7000-7099: Network errors (NetworkUnavailable, RequestTimeout, RateLimited)

Methods: `code()`, `is_retryable()`

---

## termio-server

HTTP API server built with Axum.

### Main Entry (`main.rs`)

- Initializes logging
- Loads configuration
- Creates application state
- Starts background job scheduler
- Builds router with all routes
- Listens on 127.0.0.1:8080

### Routes (`routes.rs`)

| Route | Handler | Description |
|-------|---------|-------------|
| `GET /health` | health_check | Basic health check |
| `GET /api/health` | system_health | Detailed health status |
| `GET /api/conversations` | list_conversations | List all conversations |
| `POST /api/conversations` | create_conversation | Create new conversation |
| `GET /api/conversations/:id` | get_conversation | Get conversation by ID |
| `POST /api/conversations/:id/messages` | add_message | Add message to conversation |
| `GET /api/memory` | search_memory | Search memory entries |
| `POST /api/memory` | create_memory_entry | Create memory entry |
| `POST /api/ai/chat` | chat | Chat with AI |
| `GET /api/ai/status` | ai_status | Get AI service status |
| `GET /api/notifications` | list_notifications | List notifications |
| `PUT /api/notifications/:id/dismiss` | dismiss_notification | Dismiss notification |
| `PUT /api/notifications/:id/read` | mark_notification_read | Mark as read |
| `GET /api/sync/status` | sync_status | Get sync status |
| `POST /api/sync/trigger` | trigger_sync | Trigger manual sync |
| `GET /api/plugins` | list_plugins | List installed plugins |
| `POST /api/plugins` | install_plugin | Install plugin |
| `PATCH /api/plugins/:id/toggle` | toggle_plugin | Toggle plugin |
| `DELETE /api/plugins/:id` | uninstall_plugin | Uninstall plugin |
| `GET /api/knowledge` | query_knowledge_graph | Query knowledge graph |
| `POST /api/knowledge/nodes` | create_knowledge_node | Create node |
| `POST /api/knowledge/edges` | create_knowledge_edge | Create edge |
| `GET /api/health-data` | list_health_data | List health data |
| `POST /api/health-data` | create_health_data | Create health data |
| `GET /api/action-plans` | list_action_plans | List action plans |
| `POST /api/action-plans` | create_action_plan | Create action plan |
| `PUT /api/action-plans/:id/approve` | approve_action_plan | Approve plan |
| `POST /api/action-plans/:id/execute` | execute_action_plan_step | Execute step |
| `GET /api/subscriptions` | get_subscription | Get subscription |
| `PUT /api/subscriptions` | update_subscription | Update subscription |
| `GET /api/subscriptions/plans` | list_plans | List available plans |
| `POST /webhooks/stripe` | stripe_webhook | Stripe webhook |
| `POST /webhooks/binance` | binance_webhook | Binance webhook |
| `GET /api/smart-home/devices` | list_devices | List smart devices |
| `POST /api/smart-home/devices` | add_device | Add smart device |
| `PUT /api/smart-home/devices/:id/state` | update_device_state | Update device state |
| `GET /api/smart-home/scenes` | list_scenes | List scenes |
| `POST /api/smart-home/scenes` | create_scene | Create scene |

### Middleware (`middleware/`)

- **auth**: JWT authentication middleware
- **audit**: Request/response auditing
- **sanitize**: Input sanitization
- **rate_limit**: Rate limiting

### State (`state.rs`)

- **AppState**: Shared application state with config, memory store, session manager, event bus, notification manager, health monitor

### Background Jobs (`jobs/`)

- Memory indexing
- Knowledge inference
- Proactive suggestions
- Sync polling
- Notification cleanup
- Encrypted backup
- Model optimization

---

## termio-tui

Terminal UI built with Ratatui.

### Main Entry (`main.rs`)

- Initializes logging
- Sets up crossterm terminal
- Creates app with theme
- Runs event loop with key handling

### App (`app.rs`)

Main application state and logic.

- **InputMode**: `Normal`, `Editing`
- **ActivePanel**: `Conversation`, `Context`

Features:
- Voice recording toggle (Ctrl+V)
- New conversation (Ctrl+N)
- Sidebar toggle (Ctrl+B)
- Help overlay (Ctrl+H)
- Command palette (Ctrl+K)
- Plugin manager (Ctrl+P)
- Sync trigger (Ctrl+S)
- Theme toggle (Ctrl+T)
- Panel focus switching (Tab)

### UI Rendering (`ui.rs`)

70/30 layout split per spec:

- **Conversation Panel (70%)**: Messages with markdown rendering
- **Context Panel (30%)**: Model info, memory items, graph connections

Components:
- Header with shortcuts
- Message list with user/assistant distinction
- Input area
- Status bar (sync status, notifications, mode)
- Sidebar (conversation history)
- Help overlay
- Command palette
- Plugin manager

### Theme (`theme.rs`)

iOS 26 design system colors.

- Dark theme: #0C0C0C background, #0EA5E9 accent
- Light theme: #FFFFFF background, #0EA5E9 accent
- Functional colors: success, warning, error, info

---

## Mobile App (React Native)

### Navigation (`AppNavigator.tsx`)

Bottom tab navigation:
- Home
- Assistant
- Scan
- Plugins
- Settings

Stack screens:
- Subscription
- SmartHome

### Screens

#### HomeScreen

- Header with title and notification bell
- Quick actions (New Chat, Voice Mode, Scan, Smart Home)
- Proactive suggestions carousel
- Recent conversations list
- Floating action button for new chat

#### AssistantScreen

- Chat interface with message bubbles
- Voice input button
- Text input with send button

#### ScanScreen

- Camera view for object recognition
- AR overlay support
- Results panel

#### PluginsScreen

- List of installed plugins
- Enable/disable toggles
- Marketplace link

#### SettingsScreen

- Account settings
- AI model selection
- Privacy controls
- Notifications
- Sync settings
- Help/About

#### SubscriptionScreen

- Current plan display
- Available plans (Freemium, Pro, Business, Enterprise)
- Payment methods

#### SmartHomeScreen

- Device list with on/off toggles
- Scene management
- Add device functionality

### Store (`appStore.ts`)

Zustand store for state management:

```typescript
interface AppState {
  conversations: Conversation[];
  currentConversationId: string | null;
  messages: Message[];
  // ... additional state
}
```

---

## Configuration

### Default Config (`config/default.toml`)

```toml
[app]
name = "TERMIO"
version = "1.0.0"
log_level = "info"

[ai]
max_context_tokens = 128000
inference_timeout_ms = 30000
service_url = "http://localhost:8000"
local_inference = true

[memory]
ring_buffer_size = 100
query_timeout_ms = 50
enable_embeddings = false

[server]
host = "127.0.0.1"
port = 8080
enable_cors = true

[ui]
theme = "dark"
animations = true
shortcut_prefix = "Ctrl"
```

### Environment Variables

- `TERMIO_*`: Override config values (e.g., `TERMIO_SERVER_PORT=9000`)

---

## API Reference

### Conversations

```bash
# List conversations
GET /api/conversations

# Create conversation
POST /api/conversations
{ "initial_message": "Hello" }

# Get conversation
GET /api/conversations/:id

# Add message
POST /api/conversations/:id/messages
{ "content": "Hello AI" }
```

### Memory

```bash
# Search memory
GET /api/memory?q=search&limit=10

# Create memory entry
POST /api/memory
{ "content": "Remember this", "tags": ["important"] }
```

### AI

```bash
# Chat
POST /api/ai/chat
{ "message": "Hello", "conversation_id": "optional" }

# Get AI status
GET /api/ai/status
```

### Subscriptions

```bash
# Get current subscription
GET /api/subscriptions

# Update subscription
PUT /api/subscriptions
{ "tier": "pro" }

# List available plans
GET /api/subscriptions/plans
```

---

## Security

### Encryption

- **Data at rest**: AES-256-GCM
- **Key derivation**: Argon2id (64MB memory, 3 iterations)
- **Signatures**: Ed25519 for device keys and plugin signatures

### Authentication

- JWT-based session tokens
- Device key pairs for peer authentication
- Capability-based plugin permissions

### Privacy

- On-device processing by default
- Zero data to cloud without explicit consent
- Encrypted local storage

---

## Testing

Run tests with:

```bash
# All crates
cargo test

# Specific crate
cargo test -p termio-core

# With output
cargo test -- --nocapture
```

---

## Building

```bash
# Build server
cargo build -p termio-server

# Build TUI
cargo build -p termio-tui

# Build mobile (requires React Native setup)
cd apps/mobile
npm install
npm run android  # or ios
```

---

## License

This project is proprietary software.
