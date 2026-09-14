# UI/UX Design System & Product Rationale

This document describes the design principles, information architecture, interaction states, responsive layout strategy, and accessibility choices for the **Lenny Growth Assistant**.

---

## 1. Design Philosophy & Aesthetic Principles

### 1.1 "Trust Through Provenance"
Product and growth practitioners make high-stakes bets on metrics, positioning, and retention loops. They do not trust black-box answers. Every visual decision in the interface reinforces **source provenance**:
- **Assistant Responses:** Visually anchored with warm amber branding (`#fff1dc` background, `#b86b42` icon) and explicit citation disclosures.
- **Expandable Source Drawers:** Every answer includes a clear summary pill (`"Grounded in X transcript sources"`) that expands to show the exact episode name, canonical link, and verbatim quote excerpt.
- **Defensive Restraint:** When the source corpus cannot answer a question, the UI does not attempt to disguise uncertainty—it delivers an honest, unembellished statement declining to hallucinate.

### 1.2 "Research Workspace, Not Casual Chat"
Rather than mimicking a standard consumer messenger:
- **Typography:** Uses **Newsreader** (an elegant, editorial serif) for headings and long-form essays to evoke high-value publication, paired with **DM Sans** for legible, modern UI body copy, and **DM Mono** for keyboard shortcut badges.
- **Palette:** A refined dark-navy navigation rail (`#101a35`), soft neutral canvas (`#f6f7fb`), and crisp white card containers (`#ffffff`) with subtle border definitions (`#e0e5ef`) instead of harsh black borders.
- **Side-by-Side Artifact Canvas:** When requested, generated essays and HTML cards expand side-by-side with the chat, allowing users to cross-reference research sources and the generated artifact simultaneously.

---

## 2. Information Architecture

```text
┌─────────────────┬──────────────────────────────────┬────────────────────────┐
│  Navigation     │        Conversation Canvas       │    Artifact Viewer     │
│  Rail           │                                  │    (Collapsible)       │
│                 │  [Header: Title + Model Select]  │                        │
│  • Brand Mark   ├──────────────────────────────────┤  • Kicker & Title      │
│  • New Chat     │                                  │  • Copy to Clipboard   │
│    (⌘ K)        │  • User Query Bubble             │  • Download (.md/.html)│
│  • Session List │  • Assistant Answer              │  • Close Button        │
│  • Groundedness │    └─ Expandable Citations       │                        │
│    Badge        │  • Real-time Thinking Indicator  │  • Rendered View:      │
│                 ├──────────────────────────────────┤    - Markdown Article  │
│                 │  [Composer: Artifact Toggle,     │    - Sandboxed Iframe  │
│                 │   Kind Switcher, Input, Send]    │                        │
└─────────────────┴──────────────────────────────────┴────────────────────────┘
```

---

## 3. Key Interaction States

1. **Initial Empty State (Welcome View):**
   - Welcomes the researcher with clear product framing.
   - Provides 3 one-click starter prompt chips covering core domains (Early PMF, Activation Metrics, Ship 30 Essay).
2. **Streaming & Thinking State:**
   - Subtle three-dot pulsing animation labeled `"Researching the transcripts"`.
   - Composer button disables to prevent accidental duplicate submissions.
3. **Optimistic Message Insertion:**
   - The user's message appears immediately in the message stream before network resolution, eliminating perceived latency.
4. **Actionable Error State:**
   - A dedicated dismissible alert banner appears above the composer with clear, actionable text (e.g. Ollama recovery instructions or missing key notices).
5. **Artifact Mode Active:**
   - Selecting `"Create artifact"` unveils format switcher pills (`Markdown` vs `HTML/CSS`).
   - The composer subtly highlights to indicate an artifact will be produced.
6. **Side-by-Side Artifact View:**
   - Automatically slides in from the right when an artifact is returned.
   - The topbar features a toggle button to collapse and reopen the latest artifact at any time.

---

## 4. Responsive Breakpoints & Mobile Behavior

| Viewport Width | Layout Behavior |
| --- | --- |
| **Desktop (> 1100px)** | 3-column layout: 250px fixed navigation rail, flexible chat column, and 44% width side-by-side artifact viewer. |
| **Tablet (800px – 1100px)** | Compact navigation rail (220px), flexible chat column, and 42% width artifact canvas. Starter prompts stack cleanly. |
| **Mobile (< 800px)** | Navigation rail transforms into an off-canvas drawer with slide-over animation and backdrop scrim. The artifact viewer takes over as a focused full-screen modal with an explicit close button, eliminating awkward horizontal scrolling. |

---

## 5. Accessibility (a11y) & Keyboard Navigation

- **Keyboard First:**
  - `⌘ K` (Mac) and `Ctrl + K` (Windows/Linux) immediately starts a new chat from anywhere in the app.
  - `Enter` submits the prompt; `Shift + Enter` inserts a newline.
  - Interactive elements have distinct `:focus-visible` focus rings for keyboard navigation.
- **Semantic HTML & ARIA:**
  - Proper `<main>`, `<aside>`, `<header>`, `<nav>`, and `<footer>` landmarks.
  - All icon buttons include descriptive `aria-label` attributes (`"New conversation"`, `"Copy artifact"`, `"Close navigation"`, `"Download artifact"`).
  - Status updates and error banners include `role="alert"`.
  - Contrast ratios meet or exceed WCAG 2.1 AA standards across all text elements.
