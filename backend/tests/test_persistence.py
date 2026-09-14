import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.models import ChatSession, Message, SourceDocument, TranscriptChunk
from app.schemas import SessionCreate, MessageCreate, IngestRequest, CitationOut, MessageOut


def test_chat_session_defaults():
    session = ChatSession(title="New conversation", provider="ollama")
    assert session.title == "New conversation"
    assert session.provider == "ollama"
    assert session.user_id is None


def test_message_citation_serialization():
    citation_data = {
        "title": "Casey Winters on Growth Loops",
        "source_url": "https://lenny.example.com/casey",
        "excerpt": "Growth loops are closed systems where inputs produce outputs that feed back in.",
    }
    citation = CitationOut(**citation_data)
    assert citation.title == "Casey Winters on Growth Loops"
    assert str(citation.source_url) == "https://lenny.example.com/casey"

    message = Message(
        role="assistant",
        content="Growth loops generate sustainable compounding.",
        citations=[citation.model_dump()],
    )
    assert len(message.citations) == 1
    assert message.citations[0]["title"] == "Casey Winters on Growth Loops"


def test_schema_validations():
    # Valid session
    s = SessionCreate(title="Growth chat", provider="anthropic")
    assert s.provider == "anthropic"

    # Invalid message content (empty)
    with pytest.raises(ValidationError):
        MessageCreate(content="")

    # Invalid ingest URL (malformed scheme)
    with pytest.raises(ValidationError):
        IngestRequest(source_url="not-a-valid-url")


def test_message_out_schema():
    msg_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    msg_out = MessageOut(
        id=msg_id,
        role="assistant",
        content="Answer text",
        citations=[
            CitationOut(
                title="Source Title",
                source_url="https://example.com/transcript",
                excerpt="An excerpt from transcript.",
            )
        ],
        created_at=now,
    )
    assert msg_out.id == msg_id
    assert len(msg_out.citations) == 1
    assert msg_out.citations[0].excerpt == "An excerpt from transcript."


def test_source_document_and_chunks():
    doc_id = uuid.uuid4()
    doc = SourceDocument(
        id=doc_id,
        title="Elena Verna on B2B Product-Led Growth",
        source_url="https://lenny.example.com/elena-verna",
        content_hash="abc123hash",
    )
    assert doc.id == doc_id
    assert doc.title == "Elena Verna on B2B Product-Led Growth"

    chunk = TranscriptChunk(
        document_id=doc.id,
        sequence=0,
        content="PLG is an organizational mindset...",
        embedding=[0.1] * 768,
    )
    assert chunk.sequence == 0
    assert len(chunk.embedding) == 768
