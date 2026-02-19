# TERMIO

A next-generation AI assistant that is terminal-native, offline-first, privacy-focused, and cross-platform.

## Vision

Ubiquitous private AI companion across all devices with deterministic execution and enterprise-grade security.

## Features

- **Terminal-native UI**: Beautiful TUI built with Rust and ratatui
- **Offline-first**: Full functionality without network connectivity
- **Privacy-focused**: All data encrypted, zero telemetry without consent
- **Cross-platform**: Works on macOS, Windows, and Linux

## Project Structure

```
termio/
├── crates/
│   ├── termio-core/    # Shared library (models, memory, config)
│   ├── termio-tui/     # Terminal UI application
│   └── termio-server/  # HTTP backend service
├── ai_service/            # Python FastAPI AI inference service
├── migrations/            # Database migrations
└── config/               # Configuration files
```

## Quick Start

### Prerequisites

- Rust 1.75+ with Cargo
- Python 3.11+ with Poetry
- SQLite 3.35+

### Building

```bash
# Build all Rust crates
cargo build --workspace

# Build release version
cargo build --workspace --release
```

### Running

```bash
# Run the terminal UI
cargo run -p termio-tui

# Run the backend server
cargo run -p termio-server

# Run the AI service
cd ai_service && poetry install && poetry run uvicorn src.main:app --port 8000
```

## Configuration

Configuration is loaded hierarchically:
1. Default values in code
2. `config/default.toml`
3. Environment-specific overrides
4. Environment variables (prefixed with `TERMIO_`)

## Development

```bash
# Run tests
cargo test --workspace

# Run with verbose logging
RUST_LOG=debug cargo run -p termio-tui

# Check code quality
cargo clippy --workspace -- -D warnings
cargo fmt --all -- --check
```

## License

MIT License - See LICENSE for details.
