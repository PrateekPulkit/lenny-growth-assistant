import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.artifacts import ArtifactService, SHIP30_SYSTEM
from app.services.llm import LLMService, LLMUnavailableError, GenerationResult
from app.services.retrieval import RetrievedChunk


def test_ship30_system_prompt_principles():
    assert "Ship 30 for 30" in SHIP30_SYSTEM
    assert "sharp, curiosity-provoking opening" in SHIP30_SYSTEM
    assert "one clear argument" in SHIP30_SYSTEM
    assert "concrete takeaway" in SHIP30_SYSTEM
    assert "Never manufacture examples" in SHIP30_SYSTEM
    assert "Target 450-650 words" in SHIP30_SYSTEM


@pytest.mark.asyncio
async def test_artifact_service_create_markdown():
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.answer = AsyncMock(
        return_value=GenerationResult(content="# The Retention Flywheel\n\nDeep insight...", model="test-model")
    )

    service = ArtifactService(llm=mock_llm)
    chunks = [
        RetrievedChunk(
            content="Retention drives sustainable growth.",
            title="Retention with Casey Winters",
            source_url="https://lenny.example.com/retention",
            score=0.91,
        )
    ]

    title, content = await service.create("ollama", "Write an essay on retention", chunks, "markdown")

    assert title == "Grounded growth essay"
    assert "The Retention Flywheel" in content
    mock_llm.answer.assert_awaited_once()
    called_args = mock_llm.answer.await_args
    assert "Return Markdown." in called_args.kwargs["system_override"]
    assert SHIP30_SYSTEM in called_args.kwargs["system_override"]


@pytest.mark.asyncio
async def test_artifact_service_create_html_enforces_security_constraints():
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.answer = AsyncMock(
        return_value=GenerationResult(
            content="<article><h1>Grounded Activation</h1><p>Measure milestone reach.</p></article>",
            model="test-model",
        )
    )

    service = ArtifactService(llm=mock_llm)
    title, content = await service.create("ollama", "Design an activation memo", [], "html")

    assert title == "Grounded growth artifact"
    assert "<article>" in content
    called_args = mock_llm.answer.await_args
    system_override = called_args.kwargs["system_override"]
    assert "Return a complete self-contained HTML document" in system_override
    assert "Use no scripts, forms, iframes, external assets, SVG, or event handlers" in system_override


@pytest.mark.asyncio
async def test_artifact_service_propagates_llm_unavailable():
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.answer = AsyncMock(side_effect=LLMUnavailableError("Ollama is unavailable"))

    service = ArtifactService(llm=mock_llm)
    with pytest.raises(LLMUnavailableError) as exc_info:
        await service.create("ollama", "Create essay", [], "markdown")
    assert "Ollama is unavailable" in str(exc_info.value)
