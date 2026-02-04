"""
HEDTRONIX AI Service

FastAPI application for AI inference and embeddings.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    HealthResponse,
)
from .inference import InferenceEngine
from .embeddings import EmbeddingEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global engines (initialized on startup)
inference_engine: InferenceEngine | None = None
embedding_engine: EmbeddingEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global inference_engine, embedding_engine

    logger.info("Starting HEDTRONIX AI Service...")

    # Initialize embedding engine (lightweight, always load)
    try:
        embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        embedding_engine = EmbeddingEngine(model_name=embedding_model)
        logger.info(f"Loaded embedding model: {embedding_model}")
    except Exception as e:
        logger.warning(f"Failed to load embedding model: {e}")

    # Initialize inference engine if model path is provided
    model_path = os.getenv("MODEL_PATH")
    if model_path and os.path.exists(model_path):
        try:
            inference_engine = InferenceEngine(model_path=model_path)
            logger.info(f"Loaded LLM model: {model_path}")
        except Exception as e:
            logger.warning(f"Failed to load LLM model: {e}")
    else:
        logger.info("No MODEL_PATH set, running without LLM inference")

    yield

    # Cleanup
    logger.info("Shutting down HEDTRONIX AI Service...")


# Create FastAPI app
app = FastAPI(
    title="HEDTRONIX AI Service",
    description="AI inference and embeddings for HEDTRONIX",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        model_loaded=inference_engine is not None,
        embedding_model_loaded=embedding_engine is not None,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Generate a chat response."""
    if inference_engine is None:
        # Return fallback response if no model loaded
        return ChatResponse(
            response=(
                f'I received your message: "{request.message}"\n\n'
                "The AI inference engine is not loaded. "
                "Please set MODEL_PATH to a valid GGUF model file."
            ),
            model="none",
            tokens_used=0,
            processing_time_ms=0,
        )

    try:
        import time
        start = time.time()

        response = await inference_engine.generate(
            prompt=request.message,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        processing_time_ms = int((time.time() - start) * 1000)

        return ChatResponse(
            response=response.text,
            model=inference_engine.model_name,
            tokens_used=response.tokens_used,
            processing_time_ms=processing_time_ms,
        )
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest) -> EmbeddingResponse:
    """Generate text embeddings."""
    if embedding_engine is None:
        raise HTTPException(
            status_code=503,
            detail="Embedding engine not loaded",
        )

    try:
        embeddings = await embedding_engine.encode(request.texts)
        return EmbeddingResponse(
            embeddings=embeddings,
            model=embedding_engine.model_name,
            dimensions=embedding_engine.dimensions,
        )
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
