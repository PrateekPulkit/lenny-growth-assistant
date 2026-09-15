from dataclasses import dataclass
import httpx
from anthropic import AsyncAnthropic
from app.core.config import get_settings
from app.services.retrieval import RetrievedChunk


class LLMUnavailableError(RuntimeError):
    pass


@dataclass
class GenerationResult:
    content: str
    model: str


def knowledge_prompt(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "No relevant transcript excerpts were retrieved. Say that the supplied knowledge base does not support a confident answer."
    return "\n\n".join(f"SOURCE: {chunk.title}\nURL: {chunk.source_url}\nEXCERPT: {chunk.content}" for chunk in chunks)


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def answer(self, provider: str, question: str, history: list[dict[str, str]], chunks: list[RetrievedChunk], system_override: str | None = None) -> GenerationResult:
        system = system_override or """You are The Lenny Growth Assistant, a precise internal product and growth research partner. Answer only from the supplied Lenny transcript excerpts. Do not invent facts, guests, data, or source claims. Synthesize thoughtfully, explain uncertainty, and explicitly say when the sources are insufficient. Use concise Markdown. Do not emit citations in the body; citations are added by the application."""
        context = knowledge_prompt(chunks)
        messages = history[-8:] + [{"role": "user", "content": f"Knowledge base excerpts:\n{context}\n\nQuestion: {question}"}]
        if provider == "anthropic":
            if not self.settings.anthropic_api_key:
                raise LLMUnavailableError("Anthropic is selected but ANTHROPIC_API_KEY is not configured.")
            client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)
            response = await client.messages.create(model=self.settings.anthropic_model, max_tokens=1400, system=system, messages=messages)
            return GenerationResult(content="".join(block.text for block in response.content if hasattr(block, "text")), model=self.settings.anthropic_model)
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                response = await client.post(f"{self.settings.ollama_base_url.rstrip('/')}/api/chat", json={"model": self.settings.ollama_model, "stream": False, "messages": [{"role": "system", "content": system}, *messages], "options": {"temperature": 0.2, "num_thread": 8}})
                response.raise_for_status()
                data = response.json()
                return GenerationResult(content=data["message"]["content"], model=data.get("model", self.settings.ollama_model))
        except (httpx.HTTPError, KeyError) as exc:
            raise LLMUnavailableError("Ollama is unavailable. Start Ollama and pull the configured model, or select Anthropic.") from exc
