# Coding Agent Transcript 01: Discovery, Architecture, and Foundations

**Agent:** Antigravity AI  
**Role:** Forward Deployed Systems & Full-Stack Engineer  
**Objective:** Deconstruct the "Lenny Growth Assistant" client brief, establish the core architecture, data contracts, and operational requirements.

---

## 1. Problem Framing & Discovery

### Client Context & Pain Points
The client's growth and product management teams frequently consult Lenny's Podcast transcripts to answer critical questions on product-market fit, onboarding, retention, pricing, and org design. However:
- **Search Friction:** Searching across dozens of hours of transcripts is slow and leads to missed nuance.
- **Hallucination Risk:** Generic LLM chatbots invent guest quotes, misattribute advice, or fail to provide traceable source material.
- **Format Inflexibility:** Grounded insights need to travel—executives want strategy memos, growth marketers need Ship 30-style essays, and designers want interactive HTML/CSS mockups.
- **Operational Complexity:** Internal teams do not want to manage vector indices, prompt chaining, or fragile cloud dependencies during internal evaluation.

### Core Architecture Selection
- **Backend API:** FastAPI for async I/O, type validation with Pydantic v2, and OpenAPI contract generation.
- **Frontend:** React 19 + TypeScript + Vite with vanilla scoped CSS for maximum UI fidelity and zero bloated utility overhead.
- **Knowledge Store:** PostgreSQL with `pgvector` for co-locating relational session state and vector embeddings without adding a separate vector database vendor.
- **Model Orchestration:** Dual-provider configuration:
  - **Local (Mandatory Demo):** Ollama running `llama3.2:3b` for chat and `nomic-embed-text` for 768-dim embeddings.
  - **Cloud (Production Option):** Anthropic Claude Messages API via official SDK.
- **Artifact Security:** Isolated iframe viewer with DOMPurify sanitization, strict CSP (`default-src 'none'`), and an empty iframe sandbox attribute (`sandbox=""`).

---

## 2. Iterations & Failed Attempts

### Attempt 1: Separate Vector Database vs. PostgreSQL pgvector
- **Initial Idea:** Use a standalone Pinecone or Qdrant instance for vector search and SQLite for session storage.
- **Failure / Friction:** Introducing a separate vector database created a deployment headache for local evaluation: two databases to run, synchronization failures, and complex backup/restore mechanics.
- **Correction:** Unified everything on PostgreSQL with `pgvector`. This enables ACID transactions across sessions, messages, documents, and vector embeddings in a single Docker Compose service.

### Attempt 2: Direct Client-Side Model Calls
- **Initial Idea:** Let the frontend communicate directly with Ollama on `http://localhost:11434`.
- **Failure / Friction:** Browser CORS restrictions blocked cross-origin requests from `http://localhost:8080` to port `11434`. Furthermore, cloud credentials (such as Anthropic API keys) would be exposed to browser inspection.
- **Correction:** Route all inference, embedding, and retrieval through the FastAPI backend (`/api/v1`). The client only knows the backend API; secrets and inference details remain strictly server-side.

---

## 3. Data Schema Definition
The database schema was structured into 5 cohesive entities:
1. `chat_sessions`: session UUID, title, user ID, provider enum (`ollama` | `anthropic`), timestamps.
2. `messages`: UUID, foreign key to session, role (`user` | `assistant`), content, JSONB citations snapshot, created timestamp.
3. `source_documents`: UUID, canonical source URL, title, SHA-256 content hash for idempotent re-ingestion, created timestamp.
4. `transcript_chunks`: UUID, foreign key to document, chunk sequence, text excerpt, 768-dimensional vector embedding.
5. `artifacts`: UUID, foreign key to session, title, kind (`markdown` | `html`), generated content, created timestamp.

---

## 4. Next Step
Proceed to implement transcript ingestion, chunking with overlap, vector retrieval, and LLM service routing.
