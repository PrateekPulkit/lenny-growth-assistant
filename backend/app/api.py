import logging
from datetime import datetime, timezone
from uuid import UUID
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import get_settings
from app.db import get_db
from app.models import Artifact, ChatSession, Message
from app.schemas import ArtifactOut, ChatResponse, CitationOut, HealthOut, IngestRequest, IngestResponse, MessageCreate, MessageOut, SessionCreate, SessionOut, SessionUpdate
from app.services.artifacts import ArtifactService
from app.services.llm import LLMService, LLMUnavailableError
from app.services.retrieval import RetrievalService

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


def session_out(session: ChatSession) -> SessionOut:
    return SessionOut.model_validate(session, from_attributes=True)


def message_out(message: Message) -> MessageOut:
    return MessageOut(id=message.id, role=message.role, content=message.content, citations=[CitationOut(**item) for item in (message.citations or [])], created_at=message.created_at)


@router.get("/health", response_model=HealthOut, tags=["operations"])
async def health(db: AsyncSession = Depends(get_db)) -> HealthOut:
    database = "ok"
    try:
        await db.execute(select(1))
    except Exception:
        database = "unavailable"
    ollama = "unavailable"
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            response = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
            ollama = "ok" if response.is_success else "unavailable"
    except httpx.HTTPError:
        pass
    return HealthOut(status="ok" if database == "ok" else "degraded", database=database, ollama=ollama)


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED, tags=["chat"])
async def create_session(payload: SessionCreate, db: AsyncSession = Depends(get_db)) -> SessionOut:
    session = ChatSession(title=payload.title or "New conversation", user_id=payload.user_id, provider=payload.provider or settings.default_llm_provider)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session_out(session)


@router.get("/sessions", response_model=list[SessionOut], tags=["chat"])
async def list_sessions(user_id: str | None = Query(default=None, max_length=120), db: AsyncSession = Depends(get_db)) -> list[SessionOut]:
    statement = select(ChatSession).order_by(ChatSession.updated_at.desc()).limit(50)
    if user_id:
        statement = statement.where(ChatSession.user_id == user_id)
    return [session_out(item) for item in (await db.scalars(statement)).all()]


@router.patch("/sessions/{session_id}", response_model=SessionOut, tags=["chat"])
async def update_session(session_id: UUID, payload: SessionUpdate, db: AsyncSession = Depends(get_db)) -> SessionOut:
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session was not found.")
    session.title = payload.title.strip()
    session.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return session_out(session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["chat"])
async def delete_session(session_id: UUID, db: AsyncSession = Depends(get_db)) -> None:
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session was not found.")
    await db.delete(session)
    await db.commit()


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut], tags=["chat"])
async def list_messages(session_id: UUID, db: AsyncSession = Depends(get_db)) -> list[MessageOut]:
    rows = await db.scalars(select(Message).where(Message.session_id == session_id).order_by(Message.created_at))
    return [message_out(item) for item in rows.all()]


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse, status_code=status.HTTP_201_CREATED, tags=["chat"])
async def send_message(session_id: UUID, payload: MessageCreate, db: AsyncSession = Depends(get_db)) -> ChatResponse:
    session = await db.scalar(select(ChatSession).where(ChatSession.id == session_id).options(selectinload(ChatSession.messages)))
    if not session:
        raise HTTPException(status_code=404, detail="Chat session was not found.")
    user_message = Message(session_id=session.id, role="user", content=payload.content)
    db.add(user_message)
    history = [{"role": message.role, "content": message.content} for message in session.messages]
    retrieval = RetrievalService()
    chunks = await retrieval.search(db, payload.content, settings.retrieval_top_k)
    if not chunks:
        assistant_text = "I don’t have enough indexed Lenny transcript material to answer that responsibly. Add a transcript source, then try again."
    else:
        try:
            answer = await LLMService().answer(session.provider, payload.content, history, chunks)
            assistant_text = answer.content
        except LLMUnavailableError as exc:
            logger.warning("llm_unavailable", extra={"provider": session.provider, "session_id": str(session.id)})
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    citations = [{"title": chunk.title, "source_url": chunk.source_url, "excerpt": chunk.content[:280].rstrip() + ("..." if len(chunk.content) > 280 else "")} for chunk in chunks]
    assistant = Message(session_id=session.id, role="assistant", content=assistant_text, citations=citations)
    db.add(assistant)
    if session.title == "New conversation":
        session.title = payload.content[:76].rstrip() + ("..." if len(payload.content) > 76 else "")
    session.updated_at = datetime.now(timezone.utc)
    artifact_out = None
    if payload.create_artifact:
        try:
            title, content = await ArtifactService().create(session.provider, payload.content, chunks, payload.artifact_kind)
            artifact = Artifact(session_id=session.id, title=title, kind=payload.artifact_kind, content=content)
            db.add(artifact)
            await db.flush()
            artifact_out = ArtifactOut.model_validate(artifact, from_attributes=True)
        except LLMUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    await db.commit()
    await db.refresh(assistant)
    return ChatResponse(message=message_out(assistant), artifact=artifact_out)


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED, tags=["knowledge"])
async def ingest(payload: IngestRequest, db: AsyncSession = Depends(get_db)) -> IngestResponse:
    try:
        document, count = await RetrievalService().ingest_url(db, str(payload.source_url), payload.title)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return IngestResponse(document_id=document.id, chunks_created=count, status="indexed" if count else "already_indexed")


@router.get("/sessions/{session_id}/artifacts", response_model=list[ArtifactOut], tags=["artifacts"])
async def list_artifacts(session_id: UUID, db: AsyncSession = Depends(get_db)) -> list[ArtifactOut]:
    rows = await db.scalars(select(Artifact).where(Artifact.session_id == session_id).order_by(Artifact.created_at.desc()))
    return [ArtifactOut.model_validate(item, from_attributes=True) for item in rows.all()]
