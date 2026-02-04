"""
Sentence transformer embeddings engine.
"""

import asyncio
import logging
from typing import List

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """Sentence transformer embedding engine."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize the embedding engine.

        Args:
            model_name: Name of the sentence-transformers model.
        """
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
            self.dimensions = self.model.get_sentence_embedding_dimension()
            logger.info(
                f"Loaded embedding model: {model_name} "
                f"(dimensions: {self.dimensions})"
            )

        except ImportError:
            raise RuntimeError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model: {e}")

    async def encode(self, texts: List[str]) -> List[List[float]]:
        """Encode texts into embeddings.

        Args:
            texts: List of texts to encode.

        Returns:
            List of embedding vectors.
        """
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._encode_sync(texts),
        )
        return embeddings

    def _encode_sync(self, texts: List[str]) -> List[List[float]]:
        """Synchronous encoding (runs in thread pool)."""
        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            return embeddings.tolist()

        except Exception as e:
            logger.error(f"Encoding error: {e}")
            raise

    async def encode_single(self, text: str) -> List[float]:
        """Encode a single text.

        Args:
            text: Text to encode.

        Returns:
            Embedding vector.
        """
        embeddings = await self.encode([text])
        return embeddings[0]

    def similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector.
            embedding2: Second embedding vector.

        Returns:
            Cosine similarity (0-1).
        """
        import numpy as np

        a = np.array(embedding1)
        b = np.array(embedding2)

        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
