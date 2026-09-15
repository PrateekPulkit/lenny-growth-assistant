# Master Demo Video Guide & Director's Cue Sheet (2:30 – 3:00)

This is a comprehensive, step-by-step cue sheet for recording the demonstration video for **The Lenny Growth Assistant**. It details exactly **what commands to run**, **what to click on screen**, and **what to say word-for-word** at every second.

---

## 🛠️ Phase 0: Pre-Flight Setup (Do This Before Hitting Record)

### 1. Verify Docker Stack is Running
Open PowerShell in the project directory and verify all containers are active:
```powershell
docker compose ps
```
*(If any container is stopped, run `docker compose start` and wait 5 seconds).*

### 2. Prepare Your Browser Tabs
Open Google Chrome (or your preferred browser) and set up 3 tabs:
- **Tab 1 (Main Demo):** `http://localhost:8080/` (clean state, zoom set to 100% or 110% for crisp visibility).
- **Tab 2 (API Docs):** `http://localhost:8000/docs` (FastAPI Swagger interactive documentation).
- **Tab 3 (GitHub Repo):** `https://github.com/PrateekPulkit/lenny-growth-assistant` (showing author attribution for **Prateek Pulkit** and clean commit history on `main`).

### 3. Screen Recording Setup
- **Tool:** Loom, OBS Studio, or Windows Game Bar (`Win + Alt + R`).
- **Webcam:** Turn on your camera with a talking-head overlay in the bottom-right or top-right corner.
- **Microphone:** Test audio levels so your voice is clear and crisp.
- **Clipboard:** Have the sample prompt copied so you can type or paste smoothly without typos.

---

## 🎬 Master Cue Sheet & Video Sequence

| Time | On-Screen Action | Verbatim Script (What to Say) | Visual Focus |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:25** | Start on **Tab 1** (`http://localhost:8080`). Show the sleek dark-mode UI with the brand mark and welcome hero: *"Turn conversations into product momentum"*. | *"Hi everyone, I’m Prateek Pulkit, and today I’m excited to present **The Lenny Growth Assistant**—a production-grade research workspace built for product managers, founders, and growth leads.<br><br>Teams spend countless hours searching through Lenny’s Podcast transcripts, or risking hallucinations with generic chatbots. We built this application to deliver strictly grounded answers, traceable citations, and turn raw transcript research into executive-ready Ship 30 essays and UI artifacts inside a sandboxed viewer."* | Welcome hero, branding, sidebar. |
| **0:25 – 0:50** | Point cursor to top-right model selector showing **Model: Ollama**. Point to sidebar showing recent conversations. | *"Under the hood, the entire application is containerized with Docker Compose, featuring a FastAPI async backend, PostgreSQL 16 with the pgvector extension, and a modern React 19 frontend built with TypeScript and Vite.<br><br>Critically, our AI inference runs **100% locally and privately** using Ollama—running `llama 3.2` for generation and `nomic-embed-text` for 768-dimensional vector embeddings, with instant switching to cloud Anthropic Claude when configured."* | Model selector, clean UI layout. |
| **0:50 – 1:25** | In the chat input, type or paste: `What are the signs of product market fit according to Lenny?` and press **Enter** (or click Send).<br><br>Wait for answer to render. | *"Let’s test the retrieval engine. I’ll ask: 'What are the signs of product market fit according to Lenny?'<br><br>Notice the response: instead of generic startup advice, it synthesizes the exact staged journey from Lenny’s newsletter—getting one customer to pay and love the product, expanding to multiple customers, and recognizing the critical shift from push to pull.<br><br>Now look right below the response: it features an interactive citation drawer. When I expand it..."* | Input box, streaming generation, response formatting. |
| **1:25 – 1:45** | Click **`+ Grounded in 5 transcript sources`**. Hover over the source cards showing the Substack URL and exact text excerpt. | *"...you see direct, verifiable evidence cards linking to the original Substack post, complete with verbatim excerpts. Every claim is strictly grounded in our pgvector database using cosine similarity search. If a user asks something outside the transcript corpus, the assistant explicitly declines to guess rather than hallucinating."* | Expanded citation accordion, excerpt cards, external links. |
| **1:45 – 2:05** | Check the **`Create artifact`** checkbox. Select **`Markdown`**.<br><br>Type: `Turn our PMF insights into a Ship 30 essay on finding early product momentum.` and click **Send**.<br><br>Watch the right-hand **Artifact Panel** slide open automatically! | *"Now, product insights are only valuable if they travel across an organization. I’ll check 'Create artifact', select 'Markdown', and ask for a Ship 30-style essay.<br><br>Watch the side-by-side artifact viewer slide open on the right! Our dedicated Ship 30 writing prompt structured this with a high-curiosity hook, a single core thesis, crisp H2 subheadings, bullet points for scanning, and concrete takeaways. We can copy the entire essay with one click using the built-in copy button."* | Checkbox, right split pane, rendered essay, Copy button visual checkmark. |
| **2:05 – 2:30** | 1. In chat input, type `Explain virality loops` and hit Send. Immediately point to the red pulsing **Stop button** in the composer and click it.<br>2. Hover over a conversation in the sidebar, click the ✏️ **Pencil** icon, type `PMF Masterclass` and hit **Enter**.<br>3. Hover over another chat, click 🗑️ **Trash**, show the `Delete chat? [Yes] [No]` prompt, and click **Yes**. | *"We also built full enterprise chat lifecycle controls into the workspace, just like ChatGPT or Claude.<br><br>If a response is taking too long or you want to pivot, a pulsing **Stop button** immediately cancels generation via browser AbortController without crashing the UI.<br><br>In the sidebar, you can inline rename any conversation with the pencil icon, and safely delete chats with cascading cleanup in PostgreSQL."* | Pulsing Stop button, inline edit input, delete confirm pill. |
| **2:30 – 2:55** | Switch to **Tab 2** (`http://localhost:8000/docs`) to show OpenAPI schema, then switch to **Tab 3** (`GitHub repo`). | *"From an engineering perspective, we made two critical architectural trade-offs:<br><br>First, using **PostgreSQL with pgvector** instead of a fragmented standalone vector database allowed us to maintain ACID compliance and transactional consistency across chats, messages, citations, and embeddings in one Docker stack.<br><br>Second, for HTML artifacts, we implemented a triple-layered security defense: strict system generation rules, DOMPurify sanitization, and an isolated sandbox iframe with no scripts, forms, or external asset access.<br><br>The project includes 29 automated tests covering API, persistence, RAG routing, and security."* | Swagger API routes, GitHub repository header with Prateek Pulkit attribution. |
| **2:55 – 3:05** | Look directly into the webcam with a smile. | *"The entire system is live, documented, and reproducible in one command: `docker compose up --build`.<br><br>Thank you so much for your time and consideration!"* | Webcam talking head, friendly close. |

---

## 🎯 Quick Cheat-Sheet (Keep Open on a Second Monitor)

### Prompt 1 (Retrieval & Citations):
```text
What are the signs of product market fit according to Lenny?
```

### Prompt 2 (Stop Button Demo):
```text
Explain virality loops and compounding referral engines in detail.
```
*(Hit Send, wait 2 seconds, click the Stop button).*

### Prompt 3 (Artifact Generation):
*(Check 'Create artifact' -> 'Markdown')*
```text
Turn our PMF insights into a Ship 30 essay on finding early product momentum.
```

---

## 💡 Pro Tips for a Flawless Recording
1. **Pacing:** Speak with confident, measured pacing. Don't rush; the timing above leaves 10–15 seconds of cushion.
2. **Smooth Cursor Movement:** Avoid erratic mouse circles. Move your mouse deliberately to the element you are describing.
3. **Keyboard Shortcut Bonus:** You can mention that pressing `⌘ K` or `Ctrl + K` triggers a new conversation instantly.
4. **Resolution:** Record in 1080p (1920x1080) for sharp text rendering.
