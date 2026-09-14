# System Architecture & Technical Specifications

This document outlines the architecture, database schema, data flows, security boundaries, and deployment topology of the **Lenny Growth Assistant**.

---

## 1. System Topology & Component Boundaries

```text
┌─────────────────────────────────────────────────────────────┐
│                       Client Browser                        │
│                                                             │
│   ┌─────────────────────────────┐  ┌────────────────────┐   │
│   │   React 19 + TypeScript     │  │  Sandboxed Iframe  │   │
│   │   Chat & History Canvas     │  │  (DOMPurify + CSP) │   │
│   └──────────────┬──────────────┘  └─────────▲──────────┘   │
└──────────────────┼───────────────────────────┼──────────────┘
                   │ HTTPS (JSON)              │ Local srcDoc
                   ▼                           │
┌──────────────────────────────────────────────┴──────────────┐
│                  FastAPI Backend Service                    │
│                                                             │
│   ┌──────────────┐   ┌───────────────┐   ┌──────────────┐   │
│   │  API Router  │──▶│  LLM Service  │──▶│ Artifact Svc │   │
│   │  Validation  │   │ Ollama/Claude │   │   Ship 30    │   │
│   └──────┬───────┘   └───────────────┘   └──────────────┘   │
│          │                   │                              │
│          ▼                   │                              │
│   ┌──────────────┐           │                              │
│   │  Retrieval   │◀──────────┘                              │
│   │   Service    │                                          │
│   └──────┬───────┘                                          │
└──────────┼──────────────────────────────────────────────────┘
           │
           ├────────────────────────┬─────────────────────────┐
           ▼                        ▼                         ▼
┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
│   PostgreSQL 16    │   │   Ollama Daemon    │   │   Anthropic API    │
│    + pgvector      │   │ llama3.2 / nomic   │   │   (Cloud Backup)   │
└────────────────────┘   └────────────────────┘   └────────────────────┘
```

### Component Responsibilities:
1. **Frontend (Vite / React 19):** UI rendering, state management, session switching, optimistic UI updates, Markdown rendering via `react-markdown`, and sandboxed iframe mounting. Contains zero API secrets.
2. **FastAPI Backend (`/api/v1`):** Authentication/CORS gateway, request logging with unique `X-Request-ID`, Pydantic schema validation, LLM routing, and error translation.
3. **Retrieval Service:** Document scraping with boilerplate removal, overlapping text chunking, embedding generation via Ollama (or deterministic fallback), and vector similarity search.
4. **LLM Service:** Multi-provider client abstraction supporting local Ollama and cloud Anthropic Claude with consistent system prompt enforcement and exception handling.
5. **Artifact Service:** Encodes the Ship 30 for 30 writing skill and format guardrails for Markdown essays and isolated HTML components.
6. **PostgreSQL + pgvector:** Transactional datastore storing chat sessions, messages, citations, source documents, chunk embeddings, and generated artifacts.

---

## 2. Database Schema

The database relies on PostgreSQL 16 with the `vector` extension enabled.

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. Chat Sessions
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(160) NOT NULL DEFAULT 'New conversation',
    user_id VARCHAR(120),
    provider VARCHAR(32) NOT NULL DEFAULT 'ollama',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL, -- 'user' | 'assistant'
    content TEXT NOT NULL,
    citations JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- 3. Source Documents
CREATE TABLE source_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(400) NOT NULL,
    source_url VARCHAR(2048) UNIQUE NOT NULL,
    published_at TIMESTAMPTZ,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_source_docs_hash ON source_documents(content_hash);

-- 4. Transcript Chunks
CREATE TABLE transcript_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX idx_chunks_document_id ON transcript_chunks(document_id);

-- 5. Artifacts
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    title VARCHAR(180) NOT NULL,
    kind VARCHAR(16) NOT NULL, -- 'markdown' | 'html'
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_artifacts_session_id ON artifacts(session_id);
```

---

## 3. Ingestion & Retrieval Pipeline

### Ingestion Flow:
1. **Fetch:** Client posts `POST /api/v1/ingest` with `source_url` and optional `title`.
2. **Clean:** BeautifulSoup extracts text, removing `<script>`, `<style>`, `<nav>`, `<header>`, and `<footer>` elements.
3. **Deduplication Check:** A SHA-256 hash of the cleaned text is verified against `source_documents.content_hash`. If a match is found, ingestion returns `{"status": "already_indexed", "chunks_created": 0}` with zero redundant writes.
4. **Chunking:** Text is split using an 850-character window with a 150-character overlap buffer.
5. **Embedding:** Chunks are embedded in batches using Ollama's `nomic-embed-text` (768 dimensions), or the deterministic normalized fallback if offline.
6. **Persist:** Document and chunks are committed in an ACID transaction.

### Retrieval Flow:
1. When a user asks a question, the backend embeds the question.
2. An async query calculates cosine distance (`embedding <=> query_vector`):
   ```sql
   SELECT c.content, d.title, d.source_url, (c.embedding <=> :query_vector) AS distance
   FROM transcript_chunks c
   JOIN source_documents d ON c.document_id = d.id
   ORDER BY distance ASC
   LIMIT :top_k;
   ```
3. Chunks below the distance threshold are passed as context to the LLM. If no chunks match, the assistant declines to guess.

---

## 4. Model Provider Routing

The application abstracts LLM inference behind `LLMService.answer()`:
- **Local Ollama Route:** Dispatches HTTP POST to `{OLLAMA_BASE_URL}/api/chat` with temperature 0.2. Catches connection errors and returns a structured `503 Service Unavailable`.
- **Cloud Anthropic Route:** Utilizes `AsyncAnthropic` SDK. Enforces the presence of `ANTHROPIC_API_KEY`; returns a structured `503` if missing.
- **Provider Switching:** Users can select the model provider per conversation in the UI.

---

## 5. Security Architecture

### Untrusted HTML Artifact Isolation:
Generated HTML is treated as untrusted and protected via **defense in depth**:
1. **Server-Side Rules:** The system prompt prohibits `<script>`, `<iframe>`, `<form>`, and external assets.
2. **Client-Side DOMPurify:** Strips forbidden tags (`script`, `iframe`, `object`, `embed`, `form`, `svg`, `math`) and forbidden event attributes (`onload`, `onerror`, `onclick`, `style`, `srcset`).
3. **Empty Sandbox Iframe (`sandbox=""`):** An empty sandbox attribute forces the iframe into an opaque unique origin with no capabilities:
   - Scripts are disabled (`allow-scripts` is absent).
   - Form submission is disabled (`allow-forms` is absent).
   - Top-level navigation is disabled (`allow-top-navigation` is absent).
   - Same-origin storage (cookies, localStorage) is disabled (`allow-same-origin` is absent).
4. **Content-Security-Policy:** Embedded in the iframe document:
   `default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'`

---

## 6. Deployment Topology

- **Local Deployment (Docker Compose):**
  - `db`: PostgreSQL 16 with pgvector on port 5432.
  - `ollama`: Ollama server with GPU/CPU volume persistence on port 11434.
  - `api`: FastAPI application on port 8000.
  - `web`: Nginx serving static Vite bundle on port 8080.
- **Cloud Deployment:**
  - **Frontend:** Vercel edge CDN.
  - **Backend:** Render or Railway containerized web service.
  - **Database:** Managed PostgreSQL (Supabase / Render / Neon) with pgvector extension.
