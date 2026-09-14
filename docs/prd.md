# Lenny Growth Assistant — Product Requirements Document (PRD)

## 1. Discovery Brief

### 1.1 User & Problem Framing
- **Primary Persona:** Growth Leads, Senior Product Managers, Product Marketing Managers, and Early-Stage Founders.
- **Job to Be Done:** Turn hundreds of hours of high-signal podcast transcripts into defensible strategic decisions, framework memos, and external content drafts without manual search friction or hallucination risk.
- **Pain Removed:**
  - Hours wasted skimming audio timestamps or fragmented search results.
  - Fear of ungrounded or fabricated LLM answers that quote non-existent guest statements.
  - Friction converting research insights into executive memos, Ship 30 essays, or formatted HTML concept cards.
  - Fear of managing vector databases, complex embeddings, or prompt engineering.

### 1.2 Measurable Success Metrics
1. **Adoption & Efficiency Metric:** ≥ 60% of weekly active pilot users complete a source-backed query or generate an artifact in under 5 minutes.
2. **Grounding Accuracy Metric:** ≥ 85% of generated responses rated as accurate and well-cited in pilot feedback sampling.
3. **Operational Reliability:** 99.5% uptime on the local/staging deployment, with 100% of LLM/DB connection failures producing actionable user-facing guidance (HTTP 503 error banners rather than generic crashes).

### 1.3 Key Assumptions
- **Source Rights:** The organization holds rights or permission to index public transcripts from Lenny's Podcast and Newsletter.
- **User Authentication:** Single-workspace deployment assumes users are authenticated upstream (e.g. via internal VPN, reverse proxy, or SSO). Multi-tenant IAM is therefore decoupled from this release.
- **Web Content:** Transcript URLs provide accessible HTML text with identifiable body prose.
- **Local Compute:** The evaluator's local machine runs Docker with at least 8 GB of available RAM for Ollama `llama3.2:3b`.

### 1.4 Scope Choices

| Feature Area | In Scope (Current Release) | Out of Scope (Future Phases) | Rationale |
| --- | --- | --- | --- |
| **Ingestion** | Single-URL on-demand ingestion with SHA-256 deduplication and boiler-plate cleanup. | Automated web crawling / YouTube audio transcription. | Keeps ingestion deterministic and eliminates copyright/crawling ambiguity. |
| **Model Routing** | Seamless toggle between local Ollama (`llama3.2:3b`) and cloud Anthropic (`claude-3-5-sonnet`). | Multi-agent debate / dynamic model routing by token cost. | Prioritizes rock-solid local evaluation while allowing easy production scaling. |
| **Persistence** | PostgreSQL + pgvector for ACID sessions, messages, citations, documents, and artifacts. | Multi-tenant role-based access control (RBAC). | Minimizes infrastructure surface for forward deployment pilot. |
| **Artifacts** | Dedicated Ship 30 essay skill (Markdown) and self-contained HTML/CSS mockups with safe sandboxed preview, copy, and download. | Collaborative real-time document editing (Google Docs style). | Evaluators need portable artifacts immediately; editing is done in destination tools (Notion, Google Docs). |

### 1.5 Risks & Mitigations

| Identified Risk | Severity | Mitigation Strategy |
| --- | --- | --- |
| **Hallucination** | High | Strict RAG prompt constraints; if no chunks exceed cosine similarity threshold, the model explicitly declines to answer. All valid answers attach inspectable source citation cards. |
| **Unsafe HTML Execution (XSS)** | Critical | Triple-layer defense: server-side generation rules, client-side DOMPurify sanitization, and an iframe with empty `sandbox=""` and restrictive CSP (`default-src 'none'`). |
| **Local Model Outage / Latency** | Medium | Graceful error translation: any model connection failure returns HTTP 503 with step-by-step recovery commands. Health check endpoint (`/api/v1/health`) provides instant diagnostics. |
| **Vector DB Synchronization Drift** | Medium | Unified data store: pgvector runs inside the primary PostgreSQL database, ensuring transactional consistency between document metadata and chunk embeddings. |

---

## 2. Core User Flows

### Flow 1: Grounded Research Q&A
1. User opens the application and selects their preferred model (Ollama or Anthropic).
2. User enters a query (e.g., *"How should an early-stage B2B startup measure PMF?"*).
3. Backend retrieves the top-k semantic chunks from pgvector.
4. Assistant synthesizes an answer referencing the retrieved evidence.
5. User inspects the expandable citation drawer to verify guest names, episode titles, and verbatim source excerpts.

### Flow 2: Ship 30 for 30 Content Generation
1. User activates the *"Create artifact"* toggle in composer tools.
2. User selects `"Markdown"` and asks to turn the PMF insight into an essay.
3. Dedicated `ArtifactService` applies Ship 30 writing rules (hook, 1 core idea, H2 headers, bulleted lists, concrete takeaway).
4. Artifact Viewer expands side-by-side with formatted prose.
5. User copies the Markdown directly to their clipboard or downloads `.md`.

### Flow 3: HTML/CSS Prototyping
1. User selects `"HTML/CSS"` artifact mode and asks for an onboarding metrics card.
2. Model generates self-contained semantic HTML and scoped CSS.
3. Client sanitizes content with DOMPurify and mounts inside a sandboxed iframe.
4. User inspects the interactive visual mockup safely.

---

## 3. Acceptance Criteria

- [x] **Session Isolation:** Independent chat sessions with zero history leakage.
- [x] **Strict Grounding:** Clear refusal to fabricate claims when no transcript evidence exists.
- [x] **Source Transparency:** Every grounded answer features inspectable title, URL, and excerpt cards.
- [x] **Dual Model Support:** Toggle between local Ollama and Anthropic via UI and environment configuration.
- [x] **Actionable Error States:** Missing keys or dead daemon return clean 503 banners with recovery guidance.
- [x] **XSS-Immune Artifacts:** Malicious HTML (`<script>`, `onerror`, SVG) is stripped and sandboxed.
- [x] **One-Command Boot:** Entire environment boots via `docker compose up --build`.

---

## 4. Implementation & Rollout Plan

### Phase 1: Prototype & Core Grounding (Weeks 1–2) — *Completed*
- Stand up PostgreSQL + pgvector schema and FastAPI async backend.
- Implement HTML document extraction, overlap chunking, and vector cosine search.
- Implement dual LLM orchestration (Ollama + Anthropic SDK).
- Build React 19 + TypeScript chat interface with expandable citation drawers.

### Phase 2: Content Skill & Sandbox Hardening (Weeks 3–4) — *Completed*
- Encode Ship 30 for 30 writing principles into a standalone service prompt.
- Implement side-by-side Artifact Viewer with Markdown renderer and sandboxed HTML iframe.
- Implement DOMPurify sanitization and Content-Security-Policy rules.
- Add clipboard copy, file download, and global keyboard shortcuts (`⌘ K`).

### Phase 3: Pilot Deployment & Operational Handoff (Weeks 5–6)
- Deploy backend and managed PostgreSQL on Render / Railway.
- Deploy frontend to Vercel with automated build pipeline.
- Conduct evaluator onboarding with the manual test plan (`docs/test_plan.md`).
- Monitor health endpoints and gather pilot user feedback on retrieval relevance.
