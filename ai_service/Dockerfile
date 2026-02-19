# ============================================================================
# TERMIO AI Service — Python Dockerfile
# ============================================================================

FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install pip dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e "." 2>/dev/null || \
    pip install --no-cache-dir fastapi uvicorn pydantic llama-cpp-python sentence-transformers numpy httpx

# Copy source
COPY src/ src/

# Create non-root user
RUN useradd -r -s /bin/false aiuser && chown -R aiuser:aiuser /app
USER aiuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
