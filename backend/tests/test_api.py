import uuid
from datetime import datetime, timezone
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.db import get_db
from app.models import ChatSession, Artifact
from app.services.retrieval import RetrievedChunk
from app.services.llm import LLMUnavailableError, GenerationResult


def populate_db_model(model_instance):
    if hasattr(model_instance, "id") and model_instance.id is None:
        model_instance.id = uuid.uuid4()
    if hasattr(model_instance, "created_at") and getattr(model_instance, "created_at", None) is None:
        model_instance.created_at = datetime.now(timezone.utc)
    if hasattr(model_instance, "updated_at") and getattr(model_instance, "updated_at", None) is None:
        model_instance.updated_at = datetime.now(timezone.utc)


@pytest.fixture
def mock_db():
    session = AsyncMock(spec=AsyncSession)

    def add_side_effect(instance):
        populate_db_model(instance)

    async def flush_side_effect():
        pass

    async def refresh_side_effect(instance):
        populate_db_model(instance)

    session.add = MagicMock(side_effect=add_side_effect)
    session.flush = AsyncMock(side_effect=flush_side_effect)
    session.refresh = AsyncMock(side_effect=refresh_side_effect)
    session.commit = AsyncMock()
    return session


@pytest.fixture
def test_client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    transport = httpx.ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_endpoint_healthy(test_client, mock_db):
    mock_db.execute = AsyncMock()

    mock_ollama_resp = MagicMock()
    mock_ollama_resp.is_success = True

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(return_value=mock_ollama_resp)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock()

    with patch("app.api.httpx.AsyncClient", return_value=mock_client_instance):
        response = await test_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "ok"
        assert data["ollama"] == "ok"


@pytest.mark.asyncio
async def test_health_endpoint_degraded_when_db_fails(test_client, mock_db):
    mock_db.execute = AsyncMock(side_effect=Exception("Database connection error"))

    mock_ollama_resp = MagicMock()
    mock_ollama_resp.is_success = True

    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(return_value=mock_ollama_resp)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock()

    with patch("app.api.httpx.AsyncClient", return_value=mock_client_instance):
        response = await test_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "unavailable"


@pytest.mark.asyncio
async def test_create_session(test_client, mock_db):
    session_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    def mock_add(instance):
        instance.id = session_id
        instance.created_at = now
        instance.updated_at = now

    mock_db.add = MagicMock(side_effect=mock_add)

    response = await test_client.post(
        "/api/v1/sessions",
        json={"title": "New Growth Strategy", "user_id": "analyst_1", "provider": "ollama"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Growth Strategy"
    assert data["provider"] == "ollama"
    assert data["id"] == str(session_id)


@pytest.mark.asyncio
async def test_send_message_session_not_found(test_client, mock_db):
    mock_db.scalar = AsyncMock(return_value=None)
    dummy_id = uuid.uuid4()

    response = await test_client.post(
        f"/api/v1/sessions/{dummy_id}/messages",
        json={"content": "How do we improve retention?"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_send_message_no_retrieved_chunks_unsupported_answer(test_client, mock_db):
    session_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    chat_session = ChatSession(
        id=session_id,
        title="New conversation",
        provider="ollama",
        created_at=now,
        updated_at=now,
        messages=[],
    )

    mock_db.scalar = AsyncMock(return_value=chat_session)

    with patch("app.services.retrieval.RetrievalService.search", new_callable=AsyncMock, return_value=[]):
        response = await test_client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "What is the secret recipe for quantum computing?"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "indexed Lenny transcript material" in data["message"]["content"]
        assert len(data["message"]["citations"]) == 0


@pytest.mark.asyncio
async def test_send_message_grounded_answer_with_citations(test_client, mock_db):
    session_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    chat_session = ChatSession(
        id=session_id,
        title="New conversation",
        provider="ollama",
        created_at=now,
        updated_at=now,
        messages=[],
    )

    mock_db.scalar = AsyncMock(return_value=chat_session)

    mock_chunks = [
        RetrievedChunk(
            content="To achieve product-market fit, focus on 40% 'very disappointed' metric.",
            title="Rahul Vohra on Superhuman PMF Engine",
            source_url="https://lenny.example.com/vohra",
            score=0.92,
        )
    ]

    with patch("app.services.retrieval.RetrievalService.search", new_callable=AsyncMock, return_value=mock_chunks), \
         patch("app.services.llm.LLMService.answer", new_callable=AsyncMock, return_value=GenerationResult(content="Based on Rahul Vohra's framework, measure disappointment score.", model="llama3.2:3b")):
        response = await test_client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "How did Superhuman measure PMF?"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "Rahul Vohra" in data["message"]["content"]
        assert len(data["message"]["citations"]) == 1
        assert data["message"]["citations"][0]["title"] == "Rahul Vohra on Superhuman PMF Engine"


@pytest.mark.asyncio
async def test_send_message_llm_unavailable_returns_503(test_client, mock_db):
    session_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    chat_session = ChatSession(
        id=session_id,
        title="New conversation",
        provider="ollama",
        created_at=now,
        updated_at=now,
        messages=[],
    )

    mock_db.scalar = AsyncMock(return_value=chat_session)

    mock_chunks = [
        RetrievedChunk(
            content="Grounded insight",
            title="Interview",
            source_url="https://lenny.example.com/1",
            score=0.9,
        )
    ]

    with patch("app.services.retrieval.RetrievalService.search", new_callable=AsyncMock, return_value=mock_chunks), \
         patch("app.services.llm.LLMService.answer", side_effect=LLMUnavailableError("Ollama is unavailable.")):
        response = await test_client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "Explain activation loops."},
        )
        assert response.status_code == 503
        assert "Ollama is unavailable" in response.json()["detail"]


@pytest.mark.asyncio
async def test_send_message_creates_artifact_when_requested(test_client, mock_db):
    session_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    chat_session = ChatSession(
        id=session_id,
        title="New conversation",
        provider="ollama",
        created_at=now,
        updated_at=now,
        messages=[],
    )

    mock_db.scalar = AsyncMock(return_value=chat_session)

    mock_chunks = [
        RetrievedChunk(
            content="Grounded insight",
            title="Interview",
            source_url="https://lenny.example.com/1",
            score=0.9,
        )
    ]

    with patch("app.services.retrieval.RetrievalService.search", new_callable=AsyncMock, return_value=mock_chunks), \
         patch("app.services.llm.LLMService.answer", new_callable=AsyncMock, return_value=GenerationResult(content="Summary answer", model="llama3.2:3b")), \
         patch("app.services.artifacts.ArtifactService.create", new_callable=AsyncMock, return_value=("Grounded growth essay", "# Ship 30 Essay\n\nHook...")):
        response = await test_client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={
                "content": "Turn this into an essay",
                "create_artifact": True,
                "artifact_kind": "markdown",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["artifact"] is not None
        assert data["artifact"]["title"] == "Grounded growth essay"
        assert data["artifact"]["kind"] == "markdown"
        assert "# Ship 30 Essay" in data["artifact"]["content"]


@pytest.mark.asyncio
async def test_list_artifacts_for_session(test_client, mock_db):
    session_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_artifact = Artifact(
        id=uuid.uuid4(),
        session_id=session_id,
        title="Activation Memo",
        kind="markdown",
        content="# Memo content",
        created_at=now,
    )

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_artifact]
    mock_db.scalars = AsyncMock(return_value=mock_scalars)

    response = await test_client.get(f"/api/v1/sessions/{session_id}/artifacts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Activation Memo"
