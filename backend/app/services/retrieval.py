import hashlib
import re
from dataclasses import dataclass
from bs4 import BeautifulSoup
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import SourceDocument, TranscriptChunk
from app.services.embeddings import EmbeddingService


@dataclass
class RetrievedChunk:
    content: str
    title: str
    source_url: str
    score: float


def chunk_text(text: str, size: int = 850, overlap: int = 150) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + size)
        if end < len(clean):
            boundary = clean.rfind(". ", start, end)
            if boundary > start + size // 2:
                end = boundary + 1
        part = clean[start:end].strip()
        if part:
            chunks.append(part)
        if end >= len(clean):
            break
        start = max(end - overlap, start + 1)
    return chunks


class RetrievalService:
    def __init__(self, embeddings: EmbeddingService | None = None) -> None:
        self.embeddings = embeddings or EmbeddingService()

    async def ingest_url(self, db: AsyncSession, source_url: str, title: str | None = None) -> tuple[SourceDocument, int]:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(source_url)
            response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for node in soup(["script", "style", "noscript", "nav", "footer"]):
            node.decompose()
        text = soup.get_text(" ", strip=True)
        if len(text) < 300:
            raise ValueError("The supplied source did not contain enough transcript text to index.")
        digest = hashlib.sha256(text.encode()).hexdigest()
        existing = await db.scalar(select(SourceDocument).where(SourceDocument.content_hash == digest))
        if existing:
            return existing, 0
        page_title = soup.title.string.strip() if soup.title and soup.title.string else source_url
        document = SourceDocument(title=title or page_title, source_url=source_url, content_hash=digest)
        db.add(document)
        await db.flush()
        chunks = chunk_text(text)
        for sequence, content in enumerate(chunks):
            db.add(TranscriptChunk(document_id=document.id, sequence=sequence, content=content, embedding=await self.embeddings.embed(content)))
        await db.commit()
        await db.refresh(document)
        return document, len(chunks)

    async def search(self, db: AsyncSession, query: str, limit: int = 5) -> list[RetrievedChunk]:
        embedding = await self.embeddings.embed(query)
        distance = TranscriptChunk.embedding.cosine_distance(embedding)
        result = await db.execute(
            select(TranscriptChunk, SourceDocument, distance.label("distance"))
            .join(SourceDocument, TranscriptChunk.document_id == SourceDocument.id)
            .order_by(distance)
            .limit(limit)
        )
        return [RetrievedChunk(content=chunk.content, title=document.title, source_url=document.source_url, score=max(0.0, 1 - float(row_distance))) for chunk, document, row_distance in result.all()]
