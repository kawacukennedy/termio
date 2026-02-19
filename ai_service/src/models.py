"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, Field


# ============================================================================
# Health
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    model_loaded: bool
    embedding_model_loaded: bool
    nlu_model_loaded: bool = False
    vision_model_loaded: bool = False
    stt_model_loaded: bool = False
    tts_model_loaded: bool = False
    emotion_model_loaded: bool = False


# ============================================================================
# Chat
# ============================================================================

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


# ============================================================================
# Embeddings
# ============================================================================

class EmbeddingRequest(BaseModel):
    """Embedding request."""

    texts: list[str] = Field(..., description="List of texts to embed")


class EmbeddingResponse(BaseModel):
    """Embedding response."""

    embeddings: list[list[float]]
    model: str
    dimensions: int


# ============================================================================
# NLU (FA-001 Intent Parsing)
# ============================================================================

class EntityModel(BaseModel):
    """An extracted entity."""

    entity_type: str
    value: str
    start: int
    end: int
    confidence: float = 1.0


class NluRequest(BaseModel):
    """NLU intent classification request."""

    text: str = Field(..., description="User input text to classify")


class NluResponse(BaseModel):
    """NLU intent classification response."""

    intent: str
    confidence: float
    entities: list[EntityModel] = []
    raw_text: str = ""


# ============================================================================
# Vision (FA-004 Visual Intelligence)
# ============================================================================

class VisionRequest(BaseModel):
    """Vision analysis request."""

    image_base64: str = Field(
        ..., description="Base64-encoded image data (JPEG/PNG)"
    )
    candidate_labels: list[str] | None = Field(
        default=None,
        description="Optional labels for zero-shot classification",
    )
    mode: str = Field(
        default="describe",
        description="'describe' for description, 'detect' for object detection",
    )


class DetectedObjectModel(BaseModel):
    """A detected object."""

    label: str
    confidence: float
    bounding_box: dict[str, float] | None = None


class VisionResponse(BaseModel):
    """Vision analysis response."""

    description: str
    labels: list[str] = []
    objects: list[DetectedObjectModel] = []
    confidence: float = 0.0
    model: str = ""


# ============================================================================
# Speech-to-Text (STT)
# ============================================================================

class SttRequest(BaseModel):
    """Speech-to-text request."""

    audio_base64: str = Field(..., description="Base64-encoded audio data (WAV/MP3)")
    language: str | None = Field(default=None, description="ISO language code hint")


class SttResponse(BaseModel):
    """Speech-to-text response."""

    text: str
    confidence: float = 0.0
    language_detected: str = "en"
    processing_time_ms: int = 0


# ============================================================================
# Text-to-Speech (TTS)
# ============================================================================

class TtsRequest(BaseModel):
    """Text-to-speech request."""

    text: str = Field(..., description="Text to synthesize")
    voice_id: str = Field(default="default", description="Voice ID to use")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class TtsResponse(BaseModel):
    """Text-to-speech response."""

    audio_base64: str
    format: str = "wav"
    processing_time_ms: int = 0


# ============================================================================
# Emotion Detection
# ============================================================================

class EmotionRequest(BaseModel):
    """Emotion detection request."""

    audio_base64: str = Field(..., description="Base64-encoded audio data")


class EmotionResponse(BaseModel):
    """Emotion detection response."""

    emotion: str
    confidence: float
    probabilities: dict[str, float]


# ============================================================================
# Cloud Augmentation
# ============================================================================

class AugmentRequest(BaseModel):
    """Cloud augmentation request."""

    query: str = Field(..., description="User query to augment")
    context: list[dict[str, str]] = Field(
        default_factory=list,
        description="Conversation context messages",
    )
    local_model: str = Field(default="", description="Local model used")
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for using cloud",
    )
    consent_given: bool = Field(
        default=False,
        description="Whether user has given consent for cloud processing",
    )


class AugmentResponse(BaseModel):
    """Cloud augmentation response."""

    augmented_response: str
    model_used: str
    processing_time_ms: int
    tokens_used: int


# ============================================================================
# Model Listing
# ============================================================================

class ModelInfo(BaseModel):
    """Information about a loaded model."""

    name: str
    model_type: str  # 'llm', 'embedding', 'nlu', 'vision', 'stt', 'tts', 'emotion'
    loaded: bool
    details: dict[str, str | int | float | bool] = {}


class ModelListResponse(BaseModel):
    """List of available models."""

    models: list[ModelInfo]
