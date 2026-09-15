from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import AnyHttpUrl, BaseModel, Field


class CitationOut(BaseModel):
    title: str
    source_url: str
    excerpt: str


class SessionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    user_id: str | None = Field(default=None, max_length=120)
    provider: Literal["ollama", "anthropic"] | None = None


class SessionUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=160)


class SessionOut(BaseModel):
    id: UUID
    title: str
    provider: str
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=12000)
    create_artifact: bool = False
    artifact_kind: Literal["markdown", "html"] = "markdown"


class MessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    citations: list[CitationOut] = []
    created_at: datetime


class ChatResponse(BaseModel):
    message: MessageOut
    artifact: "ArtifactOut | None" = None


class ArtifactOut(BaseModel):
    id: UUID
    title: str
    kind: Literal["markdown", "html"]
    content: str
    created_at: datetime


class IngestRequest(BaseModel):
    source_url: AnyHttpUrl
    title: str | None = Field(default=None, max_length=400)


class IngestResponse(BaseModel):
    document_id: UUID
    chunks_created: int
    status: str


class HealthOut(BaseModel):
    status: str
    database: str
    ollama: str
