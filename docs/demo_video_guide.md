# Demo Video Guide & Script (2–3 Minutes)

This script and checklist helps you record the 2–3 minute demonstration video required for Deliverable 8 of the Forward Deployed Engineer submission.

---

## Video Requirements Checklist
- **Duration:** 2 to 3 minutes.
- **Camera:** Camera / webcam enabled (talking head in the corner).
- **Core Elements to Show:**
  1. Problem explanation & client context.
  2. Live product walkthrough with local Ollama model.
  3. Source grounding & citation drawer.
  4. Ship 30 essay artifact & HTML preview.
  5. One key technical trade-off (e.g. pgvector vs standalone vector DB, or untrusted HTML sandboxing).
- **Upload:** YouTube (Unlisted or Public).

---

## 2–3 Minute Demonstration Script

### Segment 1: Problem & Architecture (0:00 – 0:35)
> *"Hi everyone, I’m presenting the Lenny Growth Assistant, an internal research workspace designed for product managers and growth leads. Teams spend hours digging through Lenny’s Podcast transcripts or risking hallucinations with generic chatbots. We built this application to solve that: it provides strictly grounded answers, traceable citations, and turns research into Ship 30 essays or HTML mockups inside a safe in-app viewer.*
>
> *Under the hood, the stack uses FastAPI, PostgreSQL with pgvector, and React with Vite. For this demo, inference and embeddings run entirely locally on Ollama using llama 3.2 and nomic-embed-text."*

### Segment 2: Local Ollama & Grounded Retrieval (0:35 – 1:20)
> *"Let's see it in action. In the top bar, you can see the model provider is set to Ollama. Let’s ask: 'How should an early-stage startup measure product-market fit?'*
>
> *(Show response generating and rendering)*
>
> *Notice two key things here: first, the answer synthesizes Rahul Vohra’s Superhuman framework. Second, look at the citation drawer: every single claim links to the specific transcript URL with an exact verbatim excerpt. If we ask something outside the corpus, like rocket fuel formulas, it explicitly declines to guess rather than hallucinating."*

### Segment 3: Ship 30 Artifact & HTML Preview (1:20 – 2:05)
> *"Now, product insights need to travel. In the composer, I’ll toggle 'Create artifact' and choose 'Markdown'. I’ll ask the assistant to turn this into a Ship 30 essay.*
>
> *(Show the side-by-side artifact viewer sliding open)*
>
> *Notice how the dedicated Ship 30 skill structured this: a sharp curiosity hook, a single core thesis, informative H2 headings, short paragraphs, selective bolding, and a concrete takeaway. We can copy the Markdown directly with one click or download it.*
>
> *We can also generate self-contained HTML/CSS components, rendered right here beside the chat."*

### Segment 4: Technical Trade-off & Security (2:05 – 2:45)
> *"One important technical trade-off was untrusted HTML rendering. Allowing raw HTML preview introduces severe XSS risks. To solve this without sacrificing user experience, we implemented a triple-layered defense: server-side generation rules, client-side DOMPurify sanitization, and an iframe with an empty sandbox attribute and a strict Content-Security-Policy that disables all scripts, forms, and external asset loading.*
>
> *Additionally, by using PostgreSQL with pgvector instead of a separate managed vector database, we maintain transactional consistency across sessions, messages, and vector embeddings in a single Docker Compose stack.*
>
> *The entire application boots with one command: docker compose up --build, and includes 27 automated tests covering the API, persistence, routing, and artifacts.*
>
> *Thank you!"*
