import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.llm import LLMService, LLMUnavailableError, GenerationResult, knowledge_prompt
from app.services.retrieval import RetrievedChunk


def test_knowledge_prompt_empty():
    assert "No relevant transcript excerpts were retrieved" in knowledge_prompt([])


def test_knowledge_prompt_with_chunks():
    chunks = [
        RetrievedChunk(
            content="To find product-market fit, talk to 30 customers.",
            title="Finding PMF with Rahul Vohra",
            source_url="https://lenny.example.com/pmf",
            score=0.88,
        )
    ]
    prompt = knowledge_prompt(chunks)
    assert "SOURCE: Finding PMF with Rahul Vohra" in prompt
    assert "URL: https://lenny.example.com/pmf" in prompt
    assert "EXCERPT: To find product-market fit" in prompt


@pytest.mark.asyncio
async def test_llm_service_anthropic_missing_api_key():
    service = LLMService()
    service.settings.anthropic_api_key = None

    with pytest.raises(LLMUnavailableError) as exc_info:
        await service.answer("anthropic", "What is PMF?", [], [])
    assert "ANTHROPIC_API_KEY is not configured" in str(exc_info.value)


@pytest.mark.asyncio
async def test_llm_service_anthropic_success():
    service = LLMService()
    service.settings.anthropic_api_key = "sk-ant-test-key"
    service.settings.anthropic_model = "claude-3-5-sonnet-20241022"

    mock_block = MagicMock()
    mock_block.text = "Grounded insight on product-market fit."
    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch("app.services.llm.AsyncAnthropic", return_value=mock_client):
        result = await service.answer("anthropic", "What is PMF?", [], [])
        assert isinstance(result, GenerationResult)
        assert result.content == "Grounded insight on product-market fit."
        assert result.model == "claude-3-5-sonnet-20241022"
        mock_client.messages.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_llm_service_ollama_success():
    service = LLMService()
    service.settings.ollama_base_url = "http://localhost:11434"
    service.settings.ollama_model = "llama3.2:3b"

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"content": "Ollama grounded response on PMF."},
        "model": "llama3.2:3b",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await service.answer("ollama", "What is PMF?", [], [])
        assert isinstance(result, GenerationResult)
        assert result.content == "Ollama grounded response on PMF."
        assert result.model == "llama3.2:3b"


@pytest.mark.asyncio
async def test_llm_service_ollama_unavailable_raises_clean_503_error():
    service = LLMService()
    service.settings.ollama_base_url = "http://localhost:11434"

    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(LLMUnavailableError) as exc_info:
            await service.answer("ollama", "What is PMF?", [], [])
        assert "Ollama is unavailable" in str(exc_info.value)
