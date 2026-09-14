from app.services.embeddings import EmbeddingService


def test_fallback_embeddings_are_deterministic_and_normalised() -> None:
    service = EmbeddingService()
    first = service._fallback_embedding("activation loops create growth")
    second = service._fallback_embedding("activation loops create growth")
    assert first == second
    assert len(first) == service.settings.embedding_dimensions
    assert round(sum(value * value for value in first), 6) == 1.0
