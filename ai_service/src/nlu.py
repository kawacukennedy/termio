"""
Natural Language Understanding (NLU) module.

Intent classification and entity extraction for TERMIO.
Implements rule-based fallback per spec (intent_parser.fallback).
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Intent categories matching spec requirements."""

    CONVERSATION = "conversation"
    ACTION_REQUEST = "action_request"
    MEMORY_QUERY = "memory_query"
    DEVICE_CONTROL = "device_control"
    HEALTH_QUERY = "health_query"
    KNOWLEDGE_QUERY = "knowledge_query"
    PLUGIN_COMMAND = "plugin_command"
    SYSTEM_COMMAND = "system_command"
    UNKNOWN = "unknown"


@dataclass
class Entity:
    """Extracted entity from user input."""

    entity_type: str
    value: str
    start: int
    end: int
    confidence: float = 1.0


@dataclass
class NluResult:
    """Result from NLU processing."""

    intent: IntentType
    confidence: float
    entities: list[Entity] = field(default_factory=list)
    raw_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# Rule-based keyword mappings for fallback classification
_INTENT_KEYWORDS: dict[IntentType, list[str]] = {
    IntentType.ACTION_REQUEST: [
        "book", "order", "send", "schedule", "create", "set",
        "open", "launch", "run", "execute", "do", "make",
        "buy", "pay", "transfer", "cancel", "delete", "remove",
    ],
    IntentType.MEMORY_QUERY: [
        "remember", "recall", "what did", "when did", "history",
        "last time", "previously", "before", "search memory",
        "find in", "look up", "forgot",
    ],
    IntentType.DEVICE_CONTROL: [
        "turn on", "turn off", "dim", "brightness", "volume",
        "lights", "thermostat", "lock", "unlock", "play",
        "pause", "stop", "smart home", "device",
    ],
    IntentType.HEALTH_QUERY: [
        "heart rate", "blood pressure", "sleep", "steps",
        "calories", "weight", "health", "fitness", "workout",
        "hrv", "spo2", "oxygen", "stress", "exercise",
    ],
    IntentType.KNOWLEDGE_QUERY: [
        "what is", "who is", "explain", "define", "tell me about",
        "how does", "why does", "knowledge", "graph", "related",
        "connection between",
    ],
    IntentType.PLUGIN_COMMAND: [
        "plugin", "install plugin", "enable plugin", "disable plugin",
        "marketplace", "extension", "add-on",
    ],
    IntentType.SYSTEM_COMMAND: [
        "settings", "configure", "sync", "backup", "update",
        "preferences", "notification", "theme", "dark mode",
        "light mode",
    ],
}

# Entity extraction patterns
_ENTITY_PATTERNS: dict[str, str] = {
    "time": r"\b(\d{1,2}:\d{2}(?:\s*[ap]m)?)\b",
    "date": r"\b(\d{4}-\d{2}-\d{2}|\b(?:today|tomorrow|yesterday|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b)",
    "number": r"\b(\d+(?:\.\d+)?)\b",
    "email": r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b",
    "url": r"(https?://[^\s]+)",
    "duration": r"\b(\d+\s*(?:minutes?|hours?|days?|weeks?|months?|seconds?))\b",
}


class IntentClassifier:
    """Rule-based intent classifier with optional ML model support.

    Falls back to rule-based classification when no ML model is loaded,
    per spec: intent_parser.fallback = 'rule-based parser'.
    """

    def __init__(self, model_path: str | None = None) -> None:
        """Initialize the intent classifier.

        Args:
            model_path: Optional path to fine-tuned classification model.
        """
        self._model = None
        self._model_loaded = False

        if model_path:
            try:
                self._load_model(model_path)
            except Exception as e:
                logger.warning(f"Failed to load NLU model, using rule-based: {e}")

    def _load_model(self, model_path: str) -> None:
        """Load a fine-tuned classification model."""
        try:
            from transformers import pipeline

            self._model = pipeline(
                "text-classification",
                model=model_path,
                top_k=3,
            )
            self._model_loaded = True
            logger.info(f"Loaded NLU model from {model_path}")
        except ImportError:
            logger.warning("transformers not installed, using rule-based NLU")
        except Exception as e:
            raise RuntimeError(f"Failed to load NLU model: {e}")

    async def classify(self, text: str) -> NluResult:
        """Classify user intent and extract entities.

        Args:
            text: User input text.

        Returns:
            NluResult with intent, confidence, and extracted entities.
        """
        entities = extract_entities(text)

        if self._model_loaded and self._model is not None:
            return await self._classify_ml(text, entities)

        return self._classify_rules(text, entities)

    async def _classify_ml(
        self, text: str, entities: list[Entity]
    ) -> NluResult:
        """Classify using ML model."""
        import asyncio

        loop = asyncio.get_event_loop()

        def _predict() -> list[dict[str, Any]]:
            assert self._model is not None
            return self._model(text)  # type: ignore[return-value]

        predictions = await loop.run_in_executor(None, _predict)

        if predictions and len(predictions) > 0:
            top = predictions[0]
            label = top.get("label", "unknown")
            score = top.get("score", 0.0)
            try:
                intent = IntentType(label)
            except ValueError:
                intent = IntentType.UNKNOWN
            return NluResult(
                intent=intent,
                confidence=score,
                entities=entities,
                raw_text=text,
            )

        return self._classify_rules(text, entities)

    def _classify_rules(
        self, text: str, entities: list[Entity]
    ) -> NluResult:
        """Rule-based intent classification (fallback)."""
        text_lower = text.lower().strip()
        best_intent = IntentType.CONVERSATION
        best_score = 0.0

        for intent, keywords in _INTENT_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                # Score based on keyword density
                score = min(matches / max(len(keywords) * 0.3, 1), 1.0)
                if score > best_score:
                    best_score = score
                    best_intent = intent

        # Default to conversation if no strong match
        if best_score < 0.15:
            best_intent = IntentType.CONVERSATION
            best_score = 0.5

        return NluResult(
            intent=best_intent,
            confidence=round(best_score, 3),
            entities=entities,
            raw_text=text,
        )

    @property
    def is_ml_loaded(self) -> bool:
        """Whether the ML model is loaded."""
        return self._model_loaded


def extract_entities(text: str) -> list[Entity]:
    """Extract entities from text using regex patterns.

    Args:
        text: Input text to extract entities from.

    Returns:
        List of extracted entities.
    """
    entities: list[Entity] = []

    for entity_type, pattern in _ENTITY_PATTERNS.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities.append(
                Entity(
                    entity_type=entity_type,
                    value=match.group(1),
                    start=match.start(1),
                    end=match.end(1),
                    confidence=0.9,
                )
            )

    return entities
