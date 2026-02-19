"""
TERMIO AI Service

FastAPI application for AI inference, embeddings, NLU, vision, STT, TTS, and emotion detection.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging
import os
import time
import base64

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    HealthResponse,
    NluRequest,
    NluResponse,
    EntityModel,
    VisionRequest,
    VisionResponse,
    DetectedObjectModel,
    AugmentRequest,
    AugmentResponse,
    SttRequest,
    SttResponse,
    TtsRequest,
    TtsResponse,
    EmotionRequest,
    EmotionResponse,
    ModelInfo,
    ModelListResponse,
)
from .inference import InferenceEngine
from .embeddings import EmbeddingEngine
from .nlu import IntentClassifier
from .vision import VisionEngine, decode_base64_image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global engines (initialized on startup)
inference_engine: InferenceEngine | None = None
embedding_engine: EmbeddingEngine | None = None
nlu_classifier: IntentClassifier | None = None
vision_engine: VisionEngine | None = None

# Placeholder flags for new services (would be real engines in full env)
stt_model_loaded: bool = False
tts_model_loaded: bool = False
emotion_model_loaded: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global inference_engine, embedding_engine, nlu_classifier, vision_engine
    global stt_model_loaded, tts_model_loaded, emotion_model_loaded

    logger.info("Starting TERMIO AI Service...")

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

    # Initialize NLU classifier
    try:
        nlu_model_path = os.getenv("NLU_MODEL_PATH")
        nlu_classifier = IntentClassifier(model_path=nlu_model_path)
        logger.info("NLU classifier initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize NLU classifier: {e}")

    # Initialize vision engine
    try:
        vision_model = os.getenv(
            "VISION_MODEL", "openai/clip-vit-base-patch32"
        )
        vision_engine = VisionEngine(clip_model=vision_model)
        logger.info(f"Vision engine initialized: {vision_model}")
    except Exception as e:
        logger.warning(f"Failed to initialize vision engine: {e}")
        
    # Check for STT/TTS models availability
    # In a real deployment, we'd load Whisper/Piper here
    if os.getenv("ENABLE_STT") == "true":
        stt_model_loaded = True
        logger.info("STT Service enabled (mock/simulated)")
        
    if os.getenv("ENABLE_TTS") == "true":
        tts_model_loaded = True
        logger.info("TTS Service enabled (mock/simulated)")
        
    if os.getenv("ENABLE_EMOTION") == "true":
        emotion_model_loaded = True
        logger.info("Emotion Detection enabled (mock/simulated)")

    yield

    # Cleanup
    logger.info("Shutting down TERMIO AI Service...")


# Create FastAPI app
app = FastAPI(
    title="TERMIO AI Service",
    description="AI inference, embeddings, NLU, vision, and speech for TERMIO",
    version="2.0.0",
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


# ============================================================================
# Health Check
# ============================================================================


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        model_loaded=inference_engine is not None,
        embedding_model_loaded=embedding_engine is not None,
        nlu_model_loaded=nlu_classifier is not None,
        vision_model_loaded=(
            vision_engine is not None and vision_engine.is_loaded
        ),
        stt_model_loaded=stt_model_loaded,
        tts_model_loaded=tts_model_loaded,
        emotion_model_loaded=emotion_model_loaded,
    )


# ============================================================================
# Chat / Inference
# ============================================================================


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


# ============================================================================
# Embeddings
# ============================================================================


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


# ============================================================================
# NLU (FA-001 Intent Classification)
# ============================================================================


@app.post("/nlu", response_model=NluResponse)
async def classify_intent(request: NluRequest) -> NluResponse:
    """Classify user intent and extract entities."""
    if nlu_classifier is None:
        raise HTTPException(
            status_code=503,
            detail="NLU classifier not initialized",
        )

    try:
        result = await nlu_classifier.classify(request.text)
        return NluResponse(
            intent=result.intent.value,
            confidence=result.confidence,
            entities=[
                EntityModel(
                    entity_type=e.entity_type,
                    value=e.value,
                    start=e.start,
                    end=e.end,
                    confidence=e.confidence,
                )
                for e in result.entities
            ],
            raw_text=result.raw_text,
        )
    except Exception as e:
        logger.error(f"NLU error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Vision (FA-004 Visual Intelligence)
# ============================================================================


@app.post("/vision", response_model=VisionResponse)
async def analyze_image(request: VisionRequest) -> VisionResponse:
    """Analyze an image — describe or detect objects."""
    if vision_engine is None or not vision_engine.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Vision engine not loaded",
        )

    try:
        image_data = decode_base64_image(request.image_base64)

        if request.mode == "detect":
            result = await vision_engine.detect_objects(
                image_data, request.candidate_labels
            )
        else:
            result = await vision_engine.describe_image(
                image_data, request.candidate_labels
            )

        return VisionResponse(
            description=result.description,
            labels=result.labels,
            objects=[
                DetectedObjectModel(
                    label=obj.label,
                    confidence=obj.confidence,
                    bounding_box=obj.bounding_box,
                )
                for obj in result.objects
            ],
            confidence=result.confidence,
            model=vision_engine.model_name,
        )
    except Exception as e:
        logger.error(f"Vision error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Speech-to-Text (STT)
# ============================================================================


# Global Whisper model (lazy loaded)
whisper_model = None


def get_whisper_model():
    """Get or initialize the Whisper model."""
    global whisper_model
    if whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            model_size = os.getenv("WHISPER_MODEL_SIZE", "tiny")
            whisper_model = WhisperModel(
                model_size,
                device="auto",
                compute_type="int8"
            )
            logger.info(f"Loaded Whisper model: {model_size}")
        except Exception as e:
            logger.warning(f"Failed to load Whisper model: {e}")
            raise
    return whisper_model


@app.post("/stt", response_model=SttResponse)
async def speech_to_text(request: SttRequest) -> SttResponse:
    """Transcribe speech to text using faster-whisper."""
    start = time.time()
    
    if len(request.audio_base64) < 100:
        raise HTTPException(status_code=400, detail="Audio data too short")
    
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(request.audio_base64)
        
        # Save to temporary file (faster-whisper needs a file path)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        try:
            # Transcribe using Whisper
            model = get_whisper_model()
            segments, info = model.transcribe(
                tmp_path,
                language=request.language,
                beam_size=5,
                vad_filter=True
            )
            
            # Collect all segments
            transcription = " ".join([seg.text for seg in segments])
            
            processing_time_ms = int((time.time() - start) * 1000)
            
            return SttResponse(
                text=transcription.strip(),
                confidence=info.language_probability if info else 0.9,
                language_detected=info.language if info else (request.language or "en"),
                processing_time_ms=processing_time_ms
            )
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"STT error: {e}")
        raise HTTPException(status_code=500, detail=f"STT processing failed: {str(e)}")


# ============================================================================
# Text-to-Speech (TTS)
# ============================================================================

# Global Piper TTS engine (lazy loaded)
piper_engine = None


def get_piper_engine():
    """Get or initialize the Piper TTS engine."""
    global piper_engine
    if piper_engine is None:
        try:
            from piper_tts import PiperTTS
            model_path = os.getenv("PIPER_MODEL_PATH", "/usr/share/piper/voices/en_US-lessac-medium.onnx")
            if not os.path.exists(model_path):
                logger.warning(f"Piper model not found at {model_path}, TTS will use fallback")
                return None
            piper_engine = PiperTTS(model_path)
            logger.info(f"Loaded Piper TTS model: {model_path}")
        except Exception as e:
            logger.warning(f"Failed to load Piper TTS: {e}")
            piper_engine = None
    return piper_engine


@app.post("/tts", response_model=TtsResponse)
async def text_to_speech(request: TtsRequest) -> TtsResponse:
    """Synthesize text to speech using Piper TTS."""
    start = time.time()
    
    try:
        engine = get_piper_engine()
        
        if engine is None:
            # Fallback: return silence placeholder
            return TtsResponse(
                audio_base64="UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAAABkYXRh",
                format="wav",
                processing_time_ms=int((time.time() - start) * 1000)
            )
        
        # Generate audio
        import io
        wav_buffer = io.BytesIO()
        engine.synthesize(request.text, wav_buffer)
        wav_bytes = wav_buffer.getvalue()
        
        # Encode to base64
        audio_base64 = base64.b64encode(wav_bytes).decode("utf-8")
        
        process_time_ms = int((time.time() - start) * 1000)
        
        return TtsResponse(
            audio_base64=audio_base64,
            format="wav",
            processing_time_ms=process_time_ms
        )
        
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS processing failed: {str(e)}")


# ============================================================================
# Emotion Detection
# ============================================================================

# Global emotion model (lazy loaded)
emotion_model = None


def get_emotion_model():
    """Get or initialize the emotion detection model."""
    global emotion_model
    if emotion_model is None:
        try:
            from transformers import pipeline
            emotion_model = pipeline(
                "audio-classification",
                model="ehcalabres/wav2vec2-lg-xlsr-53-speech-emotion-recognition",
                top_k=None
            )
            logger.info("Loaded emotion detection model")
        except Exception as e:
            logger.warning(f"Failed to load emotion model: {e}")
            emotion_model = None
    return emotion_model


@app.post("/emotion", response_model=EmotionResponse)
async def detect_emotion(request: EmotionRequest) -> EmotionResponse:
    """Detect emotion from audio using wav2vec2."""
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(request.audio_base64)
        
        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        try:
            model = get_emotion_model()
            
            if model is None:
                # Fallback to simulated response
                return EmotionResponse(
                    emotion="neutral",
                    confidence=0.85,
                    probabilities={
                        "neutral": 0.85,
                        "happy": 0.10,
                        "sad": 0.05
                    }
                )
            
            # Run emotion detection
            results = model(tmp_path)
            
            # Find the dominant emotion
            if results and len(results) > 0:
                # Results is a list of dicts with 'label' and 'score'
                top_result = max(results[0], key=lambda x: x.get("score", 0))
                emotion = top_result.get("label", "neutral").lower()
                confidence = top_result.get("score", 0.85)
                
                # Build probability distribution
                probs = {r.get("label", "unknown").lower(): r.get("score", 0) for r in results[0]}
                
                return EmotionResponse(
                    emotion=emotion,
                    confidence=confidence,
                    probabilities=probs
                )
            else:
                return EmotionResponse(
                    emotion="neutral",
                    confidence=0.85,
                    probabilities={"neutral": 0.85, "happy": 0.10, "sad": 0.05}
                )
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"Emotion detection error: {e}")
        # Return fallback on error
        return EmotionResponse(
            emotion="neutral",
            confidence=0.85,
            probabilities={
                "neutral": 0.85,
                "happy": 0.10,
                "sad": 0.05
            }
        )


# ============================================================================
# Cloud Augmentation (consent-gated proxy)
# ============================================================================


@app.post("/augment", response_model=AugmentResponse)
async def augment_with_cloud(request: AugmentRequest) -> AugmentResponse:
    """Augment a query with cloud AI (requires user consent)."""
    if not request.consent_given:
        raise HTTPException(
            status_code=403,
            detail="User consent required for cloud augmentation. "
            "Set consent_given=true to proceed.",
        )

    cloud_url = os.getenv(
        "CLOUD_AUGMENT_URL", "https://api.termio.cloud/v1/augment"
    )

    try:
        import httpx

        start = time.time()

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                cloud_url,
                json={
                    "query": request.query,
                    "context": request.context,
                    "local_model": request.local_model,
                    "confidence_threshold": request.confidence_threshold,
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Request-ID": os.urandom(16).hex(),
                },
            )

        processing_time_ms = int((time.time() - start) * 1000)

        if resp.status_code == 200:
            data = resp.json()
            return AugmentResponse(
                augmented_response=data.get("augmented_response", ""),
                model_used=data.get("model_used", "unknown"),
                processing_time_ms=processing_time_ms,
                tokens_used=data.get("tokens_used", 0),
            )
        else:
            # Cloud unavailable — return graceful degradation
            return AugmentResponse(
                augmented_response=(
                    "Cloud augmentation is currently unavailable. "
                    "Please try again later or use local inference."
                ),
                model_used="fallback",
                processing_time_ms=processing_time_ms,
                tokens_used=0,
            )

    except Exception as e:
        logger.error(f"Cloud augmentation error: {e}")
        # Graceful degradation per spec
        return AugmentResponse(
            augmented_response=(
                "Cloud augmentation failed. "
                "Falling back to local inference."
            ),
            model_used="fallback",
            processing_time_ms=0,
            tokens_used=0,
        )


# ============================================================================
# Model Listing
# ============================================================================


@app.get("/models", response_model=ModelListResponse)
async def list_models() -> ModelListResponse:
    """List all loaded AI models and their status."""
    models: list[ModelInfo] = []

    # LLM
    models.append(
        ModelInfo(
            name=(
                inference_engine.model_name if inference_engine else "none"
            ),
            model_type="llm",
            loaded=inference_engine is not None,
            details={
                "engine": "llama-cpp-python",
                "endpoint": "/chat",
            },
        )
    )

    # Embedding
    models.append(
        ModelInfo(
            name=(
                embedding_engine.model_name if embedding_engine else "none"
            ),
            model_type="embedding",
            loaded=embedding_engine is not None,
            details={
                "dimensions": (
                    embedding_engine.dimensions if embedding_engine else 0
                ),
                "endpoint": "/embeddings",
            },
        )
    )

    # NLU
    models.append(
        ModelInfo(
            name="intent-classifier",
            model_type="nlu",
            loaded=nlu_classifier is not None,
            details={
                "ml_model_loaded": (
                    nlu_classifier.is_ml_loaded if nlu_classifier else False
                ),
                "fallback": "rule-based",
                "endpoint": "/nlu",
            },
        )
    )

    # Vision
    models.append(
        ModelInfo(
            name=(
                vision_engine.model_name if vision_engine else "none"
            ),
            model_type="vision",
            loaded=(
                vision_engine is not None and vision_engine.is_loaded
            ),
            details={
                "endpoint": "/vision",
            },
        )
    )
    
    # STT
    models.append(ModelInfo(
        name="whisper-tiny-en",
        model_type="stt",
        loaded=stt_model_loaded,
        details={"engine": "whisper", "endpoint": "/stt"}
    ))
    
    # TTS
    models.append(ModelInfo(
        name="piper-en-ryan-medium",
        model_type="tts",
        loaded=tts_model_loaded,
        details={"engine": "piper", "endpoint": "/tts"}
    ))
    
    # Emotion
    models.append(ModelInfo(
        name="wav2vec2-emotion",
        model_type="emotion",
        loaded=emotion_model_loaded,
        details={"engine": "huggingface", "endpoint": "/emotion"}
    ))

    return ModelListResponse(models=models)
