# Manual Test Plan & Evaluator Quality Gates

This manual test plan guides an evaluator or QA engineer through verifying the key user flows, edge cases, resilience behaviors, and security protections of the **Lenny Growth Assistant**.

---

## 1. Prerequisites & Environment Setup

1. Clone repository and set up environment:
   ```bash
   cp .env.example .env
   docker compose up --build -d
   ```
2. Pull required Ollama models:
   ```bash
   docker compose exec ollama ollama pull llama3.2:3b
   docker compose exec ollama ollama pull nomic-embed-text
   ```
3. Verify backend health endpoint in your browser or terminal:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```
   **Expected Result:**
   ```json
   {
     "status": "ok",
     "database": "ok",
     "ollama": "ok"
   }
   ```
4. Open the web workspace at [http://localhost:8080](http://localhost:8080).

---

## 2. Test Scenarios

### Scenario 1: Starting a New Session & Keyboard Shortcuts
- **Action:**
  - Press `⌘ K` (Mac) or `Ctrl + K` (Windows/Linux), or click the `+ New conversation` button in the sidebar.
- **Expected Result:**
  - A fresh conversation session is initialized.
  - The conversation view presents the welcome canvas with starter prompt chips.
  - The URL / state reflects an isolated session ID.

---

### Scenario 2: Corpus Ingestion & Idempotency
- **Action:**
  - Ingest a public transcript page (e.g. Lenny's interview transcript):
    ```bash
    curl -X POST http://localhost:8000/api/v1/ingest \
      -H "Content-Type: application/json" \
      -d '{"source_url":"https://www.lennysnewsletter.com/p/how-to-know-if-you-have-product-market-fit","title":"How to Know If You Have Product-Market Fit"}'
    ```
- **Expected Result (First Call):**
  - Returns HTTP 201 with `{"status": "indexed", "chunks_created": N}`.
- **Action (Second Call - Idempotency Test):**
  - Run the exact same `curl` command a second time.
- **Expected Result (Second Call):**
  - Returns HTTP 201 with `{"status": "already_indexed", "chunks_created": 0}`.
  - No duplicate documents or redundant chunks are inserted into PostgreSQL.

---

### Scenario 3: Grounded Q&A with Citation Inspection
- **Action:**
  - In the chat input, ask:
    `"What are the best leading indicators for product-market fit?"`
  - Click Send or press `Enter`.
- **Expected Result:**
  - The thinking indicator activates with `"Researching the transcripts"`.
  - The assistant responds with a synthesis grounded strictly in the indexed excerpts.
  - An expandable citation box appears below the answer labeled `"Grounded in X transcript sources"`.
  - Expanding the box displays clickable source cards with the episode title, canonical link, and verbatim excerpt.

---

### Scenario 4: Non-Hallucination & Empty Corpus Handling
- **Action:**
  - Ask a question completely outside the scope of the indexed Lenny corpus (e.g. *"What is the exact formula for rocket propulsion fuel?"*).
- **Expected Result:**
  - The assistant explicitly replies:
    > *"I don’t have enough indexed Lenny transcript material to answer that responsibly. Add a transcript source, then try again."*
  - No false guest quotes or hallucinated answers are produced.

---

### Scenario 5: Multi-Session Context Isolation
- **Action:**
  - In Conversation A, ask about `"early PMF metrics"`.
  - Open a new conversation (Conversation B) via `⌘ K` and ask about `"pricing strategy"`.
  - Switch back and forth between Conversation A and Conversation B in the sidebar.
- **Expected Result:**
  - Each conversation strictly displays only its own messages and citations.
  - Context from Conversation A does not leak into Conversation B.

---

### Scenario 6: Model Provider Switching & Resilience
- **Action 1 (Model Switching):**
  - In the top bar, switch the model dropdown from `Ollama` to `Anthropic`.
  - Attempt to send a message without setting `ANTHROPIC_API_KEY` in `.env`.
- **Expected Result 1:**
  - An actionable error banner appears:
    `"Anthropic is selected but ANTHROPIC_API_KEY is not configured."`
  - The application remains stable and responsive.
- **Action 2 (Ollama Offline Simulation):**
  - Temporarily pause Ollama: `docker compose stop ollama`.
  - Send a message with the `Ollama` provider selected.
- **Expected Result 2:**
  - The UI displays an actionable HTTP 503 error banner:
    `"Ollama is unavailable. Start Ollama and pull the configured model, or select Anthropic."`
  - Restart Ollama: `docker compose start ollama`. Subsequent messages succeed.

---

### Scenario 7: Ship 30 for 30 Markdown Artifact Generation
- **Action:**
  - Toggle `"Create artifact"` in the composer tools.
  - Select `"Markdown"`.
  - Enter prompt: `"Turn this insight into a Ship 30 essay on product-market fit."`
- **Expected Result:**
  - The Artifact Viewer panel automatically expands to the right of the conversation.
  - The document header displays `"MARKDOWN ARTIFACT: Grounded growth essay"`.
  - The essay follows the Ship 30 framework: a curiosity hook, single thesis, informative H2 headings, short paragraphs, selective bolding, and a clear takeaway.
  - Clicking the **Copy** button copies the clean Markdown to clipboard and shows visual feedback.
  - Clicking the **Download** button saves a formatted `.md` file locally.

---

### Scenario 8: HTML/CSS Artifact & Sandbox Security Verification
- **Action 1 (Generate HTML Artifact):**
  - Toggle `"Create artifact"` and select `"HTML/CSS"`.
  - Ask: `"Create an HTML executive summary card for our onboarding metrics."`
- **Expected Result 1:**
  - The Artifact Viewer renders the generated HTML/CSS cleanly inside an isolated canvas.
- **Action 2 (XSS Attack Simulation):**
  - Send a prompt attempting to inject malicious script:
    `"Generate an HTML button with <script>alert('XSS')</script> and onerror=alert(1)."`
- **Expected Result 2:**
  - DOMPurify removes the `<script>` tag and `onerror` attribute before rendering.
  - The iframe's `sandbox=""` attribute and strict CSP (`default-src 'none'`) block any script execution or external asset loading.
  - Zero browser alert dialogs or parent window modifications occur.

---

### Scenario 9: Responsive Layout & Mobile Drawer
- **Action:**
  - Resize the browser window to under 800px width.
- **Expected Result:**
  - The sidebar collapses into a slide-over mobile drawer accessed via the hamburger menu.
  - When an artifact is opened, it renders as a focused full-screen view with an easy close button, preventing cramped split views on small screens.
