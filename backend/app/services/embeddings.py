import hashlib
import math
from collections import Counter
import httpx
from app.core.config import get_settings


class EmbeddingService:
    """Uses Ollama embeddings in production and deterministic vectors for unavailable local demos."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def _fallback_embedding(self, text: str) -> list[float]:
        vector = [0.0] * self.settings.embedding_dimensions
        counts = Counter(token.lower() for token in text.split() if token.strip())
        for token, count in counts.items():
            index = int(hashlib.sha256(token.encode()).hexdigest(), 16) % len(vector)
            vector[index] += float(count)
        magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / magnitude for value in vector]

    async def embed(self, text: str) -> list[float]:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    f"{self.settings.ollama_base_url.rstrip('/')}/api/embed",
                    json={"model": "nomic-embed-text", "input": text},
                )
                response.raise_for_status()
                embedding = response.json()["embeddings"][0]
                if len(embedding) == self.settings.embedding_dimensions:
                    return embedding
        except (httpx.HTTPError, KeyError, IndexError):
            pass
        return self._fallback_embedding(text)
