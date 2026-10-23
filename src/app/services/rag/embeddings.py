import logging
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np

from src.app.core.config import get_settings
from src.app.core.exceptions import EmbeddingError, LLMConfigurationError

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseEmbeddingProvider(ABC):
    """Abstract interface for real embedding generation."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Embeds a single text string into a normalized dense vector."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embeds a batch of text strings into normalized dense vectors."""
        pass


class SentenceTransformersProvider(BaseEmbeddingProvider):
    """Generates dense embeddings locally using SentenceTransformers models."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None

    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(f"Loading SentenceTransformers model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.error(f"Failed to load embedding model '{self.model_name}': {e}", exc_info=True)
                raise EmbeddingError(
                    f"Failed to initialize embedding model '{self.model_name}': {e}",
                    details={"model_name": self.model_name},
                )
        return self._model

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed empty text.")
        try:
            vector = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            return vector.tolist()
        except Exception as e:
            logger.error(f"SentenceTransformers embedding failed: {e}", exc_info=True)
            raise EmbeddingError(f"Embedding generation failed: {e}")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            # Replace empty strings with a single space to avoid tokenizer errors
            safe_texts = [t if t and t.strip() else " " for t in texts]
            vectors = self.model.encode(
                safe_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return [v.tolist() for v in vectors]
        except Exception as e:
            logger.error(f"SentenceTransformers batch embedding failed: {e}", exc_info=True)
            raise EmbeddingError(f"Batch embedding generation failed: {e}")


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Generates embeddings via Google Gemini GenAI API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "models/text-embedding-004"):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = settings.GEMINI_API_KEY
        self.model = model
        if not self.api_key or self.api_key.startswith("mock_"):
            raise LLMConfigurationError("Valid GEMINI_API_KEY is required for Gemini embedding provider.")

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed empty text.")
        try:
            from google import genai

            client = genai.Client(api_key=self.api_key)
            result = client.models.embed_content(
                model=self.model,
                contents=text,
            )
            embedding = result.embedding.values
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = [float(x / norm) for x in embedding]
            return embedding
        except Exception as e:
            logger.error(f"Gemini embedding API call failed: {e}", exc_info=True)
            raise EmbeddingError(f"Gemini embedding generation failed: {e}")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            from google import genai

            client = genai.Client(api_key=self.api_key)
            result = client.models.embed_content(
                model=self.model,
                contents=texts,
            )
            embeddings = []
            for item in result.embeddings:
                emb = item.values
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = [float(x / norm) for x in emb]
                embeddings.append(emb)
            return embeddings
        except Exception as e:
            logger.error(f"Gemini batch embedding API call failed: {e}", exc_info=True)
            raise EmbeddingError(f"Gemini batch embedding generation failed: {e}")


_cached_embedding_service: Optional[BaseEmbeddingProvider] = None


def get_embedding_service() -> BaseEmbeddingProvider:
    """Returns singleton instance of the configured embedding provider."""
    global _cached_embedding_service
    if _cached_embedding_service is None:
        provider = settings.EMBEDDING_PROVIDER.lower()
        if provider == "gemini":
            _cached_embedding_service = GeminiEmbeddingProvider()
        else:
            _cached_embedding_service = SentenceTransformersProvider()
    return _cached_embedding_service
