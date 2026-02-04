# HEDTRONIX AI Service

FastAPI-based AI inference service for HEDTRONIX.

## Setup

```bash
# Install dependencies
poetry install

# Run the service
poetry run uvicorn src.main:app --reload --port 8000
```

## Endpoints

- `GET /health` - Health check
- `POST /chat` - Chat with the AI
- `POST /embeddings` - Generate text embeddings

## Configuration

Set environment variables:

- `MODEL_PATH` - Path to GGUF model file
- `EMBEDDING_MODEL` - Sentence transformer model name
