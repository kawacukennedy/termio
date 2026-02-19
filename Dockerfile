# ============================================================================
# TERMIO Server — Multi-stage Docker Build
# ============================================================================

# Stage 1: Builder
FROM rust:1.76-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    cmake \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Copy workspace manifests for dependency caching
COPY Cargo.toml Cargo.lock ./
COPY crates/termio-core/Cargo.toml crates/termio-core/
COPY crates/termio-server/Cargo.toml crates/termio-server/
COPY crates/termio-tui/Cargo.toml crates/termio-tui/

# Create dummy source files to build dependencies
RUN mkdir -p crates/termio-core/src && echo "pub fn dummy() {}" > crates/termio-core/src/lib.rs && \
    mkdir -p crates/termio-server/src && echo "fn main() {}" > crates/termio-server/src/main.rs && \
    mkdir -p crates/termio-tui/src && echo "fn main() {}" > crates/termio-tui/src/main.rs

# Build dependencies (cached layer)
RUN cargo build --release -p termio-server 2>/dev/null || true

# Copy actual source code
COPY crates/ crates/
COPY config/ config/
COPY migrations/ migrations/

# Build the server binary
RUN touch crates/termio-core/src/lib.rs crates/termio-server/src/main.rs && \
    cargo build --release -p termio-server

# Stage 2: Runtime
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -r -s /bin/false termio

WORKDIR /app

# Copy binary and config
COPY --from=builder /app/target/release/termio-server .
COPY config/ config/
COPY migrations/ migrations/

# Set ownership
RUN chown -R termio:termio /app

USER termio

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Run
CMD ["./termio-server"]
