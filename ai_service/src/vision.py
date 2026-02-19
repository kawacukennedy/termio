"""
Visual Intelligence module (FA-004).

Image description and object detection using CLIP.
Graceful fallback when vision models are unavailable.
"""

import asyncio
import base64
import logging
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DetectedObject:
    """A detected object in an image."""

    label: str
    confidence: float
    bounding_box: dict[str, float] | None = None  # x, y, width, height


@dataclass
class VisionResult:
    """Result from vision processing."""

    description: str
    objects: list[DetectedObject] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class VisionEngine:
    """Vision engine using CLIP for image understanding.

    Supports:
    - Image description (zero-shot classification with candidate labels)
    - Object detection / label classification
    - Graceful degradation when models unavailable
    """

    def __init__(
        self,
        clip_model: str = "openai/clip-vit-base-patch32",
    ) -> None:
        """Initialize the vision engine.

        Args:
            clip_model: HuggingFace CLIP model name.
        """
        self._model = None
        self._processor = None
        self._model_loaded = False
        self.model_name = clip_model

        try:
            self._load_model(clip_model)
        except Exception as e:
            logger.warning(f"Vision engine unavailable: {e}")

    def _load_model(self, model_name: str) -> None:
        """Load CLIP model and processor."""
        try:
            from transformers import CLIPModel, CLIPProcessor

            self._processor = CLIPProcessor.from_pretrained(model_name)
            self._model = CLIPModel.from_pretrained(model_name)
            self._model_loaded = True
            logger.info(f"Loaded vision model: {model_name}")
        except ImportError:
            logger.warning(
                "transformers not installed. "
                "Install with: pip install transformers torch"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load vision model: {e}")

    async def describe_image(
        self,
        image_data: bytes,
        candidate_labels: list[str] | None = None,
    ) -> VisionResult:
        """Describe an image using zero-shot classification.

        Args:
            image_data: Raw image bytes (JPEG/PNG).
            candidate_labels: Labels to classify against. If None, uses defaults.

        Returns:
            VisionResult with description and labels.
        """
        if not self._model_loaded:
            return VisionResult(
                description="Vision model not loaded. Cannot process image.",
                confidence=0.0,
                metadata={"error": "model_not_loaded"},
            )

        if candidate_labels is None:
            candidate_labels = [
                "a photograph", "a document", "a chart or graph",
                "a person", "text or handwriting", "food",
                "a landscape", "an animal", "a building",
                "a vehicle", "electronics", "furniture",
                "medical image", "a screenshot",
            ]

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._classify_sync(image_data, candidate_labels),
        )
        return result

    async def detect_objects(
        self,
        image_data: bytes,
        object_labels: list[str] | None = None,
    ) -> VisionResult:
        """Detect objects in an image.

        Uses CLIP for zero-shot object classification.

        Args:
            image_data: Raw image bytes.
            object_labels: Object types to look for. Uses defaults if None.

        Returns:
            VisionResult with detected objects.
        """
        if not self._model_loaded:
            return VisionResult(
                description="Vision model not loaded.",
                confidence=0.0,
                metadata={"error": "model_not_loaded"},
            )

        if object_labels is None:
            object_labels = [
                "person", "car", "phone", "laptop", "book",
                "cup", "chair", "table", "plant", "food",
                "dog", "cat", "building", "sign", "screen",
            ]

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._detect_sync(image_data, object_labels),
        )
        return result

    def _classify_sync(
        self,
        image_data: bytes,
        candidate_labels: list[str],
    ) -> VisionResult:
        """Synchronous CLIP classification."""
        try:
            from PIL import Image
            import torch

            image = Image.open(BytesIO(image_data)).convert("RGB")

            inputs = self._processor(
                text=candidate_labels,
                images=image,
                return_tensors="pt",
                padding=True,
            )

            with torch.no_grad():
                outputs = self._model(**inputs)

            logits = outputs.logits_per_image[0]
            probs = logits.softmax(dim=0)

            # Get top results
            sorted_indices = probs.argsort(descending=True)
            top_labels: list[str] = []
            top_scores: list[float] = []

            for idx in sorted_indices[:5]:
                label = candidate_labels[idx]
                score = probs[idx].item()
                if score > 0.05:  # threshold
                    top_labels.append(label)
                    top_scores.append(round(score, 4))

            description_parts = []
            if top_labels:
                description_parts.append(
                    f"This appears to be {top_labels[0]} "
                    f"(confidence: {top_scores[0]:.1%})"
                )
                if len(top_labels) > 1:
                    others = ", ".join(top_labels[1:3])
                    description_parts.append(f"Also resembles: {others}")

            return VisionResult(
                description=". ".join(description_parts) if description_parts else "Unable to classify image.",
                labels=top_labels,
                confidence=top_scores[0] if top_scores else 0.0,
                metadata={
                    "scores": dict(zip(top_labels, top_scores)),
                    "model": self.model_name,
                },
            )

        except Exception as e:
            logger.error(f"Vision classification error: {e}")
            return VisionResult(
                description=f"Error processing image: {e}",
                confidence=0.0,
                metadata={"error": str(e)},
            )

    def _detect_sync(
        self,
        image_data: bytes,
        object_labels: list[str],
    ) -> VisionResult:
        """Synchronous object detection using CLIP."""
        try:
            from PIL import Image
            import torch

            image = Image.open(BytesIO(image_data)).convert("RGB")

            inputs = self._processor(
                text=object_labels,
                images=image,
                return_tensors="pt",
                padding=True,
            )

            with torch.no_grad():
                outputs = self._model(**inputs)

            logits = outputs.logits_per_image[0]
            probs = logits.softmax(dim=0)

            detected: list[DetectedObject] = []
            for idx, label in enumerate(object_labels):
                score = probs[idx].item()
                if score > 0.1:  # detection threshold
                    detected.append(
                        DetectedObject(
                            label=label,
                            confidence=round(score, 4),
                        )
                    )

            detected.sort(key=lambda d: d.confidence, reverse=True)

            labels = [d.label for d in detected]
            top_conf = detected[0].confidence if detected else 0.0

            return VisionResult(
                description=f"Detected {len(detected)} object(s): {', '.join(labels[:5])}" if detected else "No objects detected.",
                objects=detected,
                labels=labels,
                confidence=top_conf,
                metadata={"model": self.model_name},
            )

        except Exception as e:
            logger.error(f"Object detection error: {e}")
            return VisionResult(
                description=f"Error detecting objects: {e}",
                confidence=0.0,
                metadata={"error": str(e)},
            )

    @property
    def is_loaded(self) -> bool:
        """Whether the vision model is loaded."""
        return self._model_loaded


def decode_base64_image(b64_string: str) -> bytes:
    """Decode a base64-encoded image string to bytes.

    Args:
        b64_string: Base64-encoded image data.

    Returns:
        Raw image bytes.
    """
    # Strip data URI prefix if present
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]
    return base64.b64decode(b64_string)
