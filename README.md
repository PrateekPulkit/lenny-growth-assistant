# Lenny Growth Assistant

> **Engineered with precision by [Prateek Pulkit](https://github.com/PrateekPulkit)**  
> *Forward Deployed Systems & Full-Stack Engineering Assignment*

A production-minded, source-grounded product and growth research workspace built for Lenny's Podcast transcripts. It combines persistent chat, cited retrieval, model switching, Ship 30-style writing artifacts, and a safe in-app artifact viewer.

![Author](https://img.shields.io/badge/Author-Prateek%20Pulkit-d77c47?style=flat&logo=github) ![Architecture](https://img.shields.io/badge/architecture-FastAPI%20%2B%20React-243b68) ![Local model](https://img.shields.io/badge/local%20model-Ollama-7c4dff) ![Database](https://img.shields.io/badge/database-PostgreSQL%20%2B%20pgvector-4169e1)

## Why it exists

Product and growth teams need usable, defensible insight—not another ungrounded chatbot. The assistant retrieves relevant transcript excerpts before generating an answer, keeps conversations isolated, and gives each answer inspectable source cards. When insight needs to travel, the same grounded research can become a structured Markdown or HTML/CSS artifact directly inside the workspace.

## Product highlights

- **Transcript-grounded RAG:** chunks and embeds source pages, performs pgvector cosine retrieval, and attaches sources to each response.
- **Model flexibility:** the default demo uses Ollama. Anthropic is available through the same agent interface when an API key is configured.
- **Persistent, isolated chats:** PostgreSQL stores sessions, user metadata, messages, citations, and artifacts.
- **A real content skill:** Ship 30-style writing rules are encoded in a dedicated artifact service rather than hidden in an ad hoc prompt.
- **Safe artifacts:** generated HTML is sanitized, protected by a resource-blocking CSP, and rendered in an iframe with an empty sandbox; scripts, forms, frames, embeds, SVG, MathML, external assets, and event attributes are blocked.
- **Operationally ready:** one command local startup, health endpoint, CORS allowlist, structured request logging, actionable failure messages, and source hashing for idempotent ingestion.

## Architecture

```text
Browser (React / Vite)
       │  VITE_API_URL
       ▼
FastAPI API ───── PostgreSQL + pgvector
       │                 ▲
       ├── Ollama ───────┘
       └── Anthropic API (optional)
```

See [architecture details](docs/architecture.md), [product requirements](docs/prd.md), and [UX decisions](docs/design.md).

## Quick start

### Prerequisites

- Docker Desktop with Docker Compose v2
- At least 8 GB of free RAM for the recommended Ollama model (more is better)

### Run locally

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull nomic-embed-text
```

Open [http://localhost:8080](http://localhost:8080). The API health check is at [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health).

To stop the stack, use `docker compose down`. To remove local database and model volumes as well, use `docker compose down -v`.

### Add transcript sources

The corpus starts empty by design—this avoids committing scraped or unverified material. Index a permitted transcript URL through the API:

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"source_url":"https://your-permitted-transcript-source.example/episode","title":"Episode title"}'
```

The ingestion service strips boilerplate, chunks content with overlap, embeds each chunk, records a content hash, and preserves the canonical URL for citation. Reposting unchanged content is safely idempotent.

## Configuration

Copy `.env.example` to `.env`; never commit the latter.

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Yes outside Compose | Async PostgreSQL connection string. |
| `DEFAULT_LLM_PROVIDER` | No | `ollama` (default) or `anthropic`. |
| `OLLAMA_BASE_URL` | Ollama | Ollama server URL. |
| `OLLAMA_MODEL` | Ollama | Chat model, default `llama3.2:3b`. |
| `ANTHROPIC_API_KEY` | Anthropic | Cloud provider credential, kept server-side only. |
| `ANTHROPIC_MODEL` | No | Cloud model ID. |
| `ALLOWED_ORIGINS` | Production | Comma-separated browser origins allowed to call the API. |
| `VITE_API_URL` | Production frontend | Public API prefix, e.g. `https://api.example.com/api/v1`. |

If Ollama is offline, chat returns a clear `503` telling the operator how to recover. If Anthropic is selected without a key, the same happens. The UI keeps the chosen provider visible so evaluators can verify the route.

## API contracts

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Dependency status for database and Ollama. |
| `POST` | `/api/v1/sessions` | Create an isolated chat session. |
| `GET` | `/api/v1/sessions` | List recent sessions. |
| `GET` | `/api/v1/sessions/{id}/messages` | Read persisted conversation history. |
| `POST` | `/api/v1/sessions/{id}/messages` | Send a grounded question and optionally create an artifact. |
| `POST` | `/api/v1/ingest` | Ingest a permitted transcript webpage. |
| `GET` | `/api/v1/sessions/{id}/artifacts` | Read session artifacts. |

FastAPI provides an interactive contract explorer at `/docs` while the API is running.

## Testing and quality gates

The repository includes a comprehensive 27-test automated regression suite covering critical API endpoints, session persistence, LLM provider routing, Ship 30 artifact formatting, fallback embeddings, and retrieval:

```bash
cd backend
python -m pytest
python -m ruff check app tests
```

For the frontend:

```bash
cd frontend
npm install
npm run lint
npm run build
```

For evaluator manual quality assurance and UI flow validation, consult the [Manual Test Plan](docs/test_plan.md).

## Project deliverables

| Deliverable | Location | Description |
| --- | --- | --- |
| **Source Code** | `/backend`, `/frontend` | Complete FastAPI + PostgreSQL/pgvector + React 19 codebase. |
| **README** | `README.md` | Setup guide, architecture summary, and operational troubleshooting. |
| **PRD** | [docs/prd.md](docs/prd.md) | Discovery brief, personas, metrics, assumptions, scope, flows, and rollout plan. |
| **Design Doc** | [docs/design.md](docs/design.md) | UI/UX rationale, IA, interaction states, accessibility, and responsive behavior. |
| **Architecture** | [docs/architecture.md](docs/architecture.md) | System boundaries, DDL schema, API contracts, security, and topology. |
| **Agent Transcripts** | [agent-transcripts/](agent-transcripts/) | 4 sanitized transcripts covering discovery, RAG, artifacts, and test resolution. |
| **Test Plan** | [docs/test_plan.md](docs/test_plan.md) | 9 step-by-step evaluator scenarios for UI, security, and resilience. |
| **Demo Video Guide** | [docs/demo_video_guide.md](docs/demo_video_guide.md) | 2–3 minute video script and recording checklist. |

## Deployment

### Recommended: Vercel for web + Render for API + managed Postgres

1. Push this repository to GitHub.
2. Create a Render PostgreSQL database with `pgvector` available, then deploy the API from this repo using `render.yaml` or the `backend/Dockerfile`.
3. Set the API's `DATABASE_URL`, `ANTHROPIC_API_KEY` if using cloud inference, and `ALLOWED_ORIGINS` to the future Vercel URL. For a serverless API, use Anthropic; Ollama requires a persistent machine with adequate RAM.
4. In Vercel, import the repository. Set the root directory to `frontend`, build command to `npm run build`, output directory to `dist`, and `VITE_API_URL` to `https://YOUR-RENDER-SERVICE.onrender.com/api/v1`.
5. Redeploy the API once the Vercel URL is known so its CORS allowlist includes that origin.
6. Open `/api/v1/health`, ingest an approved source, and complete the release checks above.

### GitHub Pages

GitHub Pages can host only the static Vite frontend; it cannot run FastAPI, PostgreSQL, or Ollama. Deploy the API separately (Render, Railway, Fly.io, or a VM) and use the Vite environment variable `VITE_API_URL` at build time. The included `vercel.json` is for Vercel; a Pages workflow can use `npm ci && npm run build` in `frontend` and publish `frontend/dist`.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| API cannot connect to DB | Confirm `db` is healthy with `docker compose ps`; use the Compose `DATABASE_URL`, not `localhost`, from inside containers. |
| Ollama returns 503 | Run the two `ollama pull` commands above and check `docker compose logs ollama`. |
| Ingestion returns 422 | Confirm the URL is a public, permitted transcript page with at least 300 characters of readable text. |
| Answers have no citations | Index a source first; inspect the source URL and confirm it contains transcript text. |
| Browser blocks API request | Add the exact frontend origin to `ALLOWED_ORIGINS`; restart the API. |
| HTML preview looks plain | This is intentional when unsafe tags/attributes are stripped. The viewer blocks executable or externally embedded content. |

## Handoff and extension paths

The code separates retrieval, LLM routing, artifacts, and API contracts to keep future work contained. Natural next steps are upstream authentication, a protected admin ingestion screen, queue-backed ingestion, user feedback capture, source-level retention controls, model latency/cost metrics, and a source refresh scheduler. See the PRD for intentional scope boundaries and the architecture document for component ownership.

---

## Author & Engineering Lead

**Designed, engineered, and delivered by [Prateek Pulkit](https://github.com/PrateekPulkit)**  
*Forward Deployed Systems & Full-Stack Engineer*  
GitHub: [@PrateekPulkit](https://github.com/PrateekPulkit)

