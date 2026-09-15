from app.services.llm import LLMService
from app.services.retrieval import RetrievedChunk

SHIP30_SYSTEM = """You are a Ship 30 for 30 writing skill. Turn only the supplied grounded research into a useful essay. Use a sharp, curiosity-provoking opening; make one clear argument; use informative H2 headings, short paragraphs, bullets only when they improve scanning, and selective bold emphasis. End with a concrete takeaway. Never manufacture examples, statistics, or source claims. Target 450-650 words with crisp, atomic takeaways unless the evidence is too thin, in which case say so. Return only the requested artifact, no code fence."""


class ArtifactService:
    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or LLMService()

    async def create(self, provider: str, request: str, chunks: list[RetrievedChunk], kind: str) -> tuple[str, str]:
        format_rule = "Return Markdown." if kind == "markdown" else "Return a complete self-contained HTML document. Use no scripts, forms, iframes, external assets, SVG, or event handlers. Use semantic HTML and scoped CSS only."
        result = await self.llm.answer(provider, request, [], chunks, system_override=f"{SHIP30_SYSTEM}\n\n{format_rule}")
        title = "Grounded growth essay" if kind == "markdown" else "Grounded growth artifact"
        return title, result.content
