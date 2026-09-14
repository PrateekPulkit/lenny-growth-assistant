from app.services.retrieval import chunk_text


def test_chunk_text_keeps_content_and_uses_overlap() -> None:
    text = "Sentence one. " * 200
    chunks = chunk_text(text, size=100, overlap=20)
    assert len(chunks) > 3
    assert all(chunk.strip() for chunk in chunks)
    assert "Sentence one" in chunks[0]


def test_chunk_text_handles_short_content() -> None:
    assert chunk_text("One useful transcript excerpt.") == ["One useful transcript excerpt."]
