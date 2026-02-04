"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    model_loaded: bool
    embedding_model_loaded: bool


class ChatRequest(BaseModel):
    """Chat request."""

    message: str = Field(..., description="User message to respond to")
    max_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    system_prompt: str | None = Field(
        default=None,
        description="Optional system prompt to set AI behavior",
    )


class ChatResponse(BaseModel):
    """Chat response."""

    response: str
    model: str
    tokens_used: int
    processing_time_ms: int


class EmbeddingRequest(BaseModel):
    """Embedding request."""

    texts: list[str] = Field(..., description="List of texts to embed")


class EmbeddingResponse(BaseModel):
    """Embedding response."""

    embeddings: list[list[float]]
    model: str
    dimensions: int
