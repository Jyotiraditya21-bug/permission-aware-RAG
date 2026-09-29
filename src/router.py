"""Query routing and decomposition."""
from pathlib import Path
from typing import Protocol

from src.models import Route

PROMPTS_DIR = Path(__file__).parent / "prompts"


class LLMClient(Protocol):
    async def generate(self, prompt: str, input_text: str) -> str:
        ...


class QueryRouter:
    def __init__(self, llm: LLMClient, max_subqueries: int = 3) -> None:
        self.llm = llm
        self.max_subqueries = max_subqueries
        self._router_prompt = (PROMPTS_DIR / "router.md").read_text()
        self._decompose_prompt = (PROMPTS_DIR / "decompose.md").read_text().format(
            max_subqueries=max_subqueries
        )

    async def route(self, query: str) -> Route:
        """Route the query to direct-retrieve, decompose, or no-retrieval-needed."""
        try:
            response = await self.llm.generate(self._router_prompt, query)
            response = response.strip()
            if response in ("direct-retrieve", "decompose", "no-retrieval-needed"):
                return response  # type: ignore
        except Exception:
            pass
        # Fallback for ambiguous/failing routing is direct retrieval
        return "direct-retrieve"

    async def decompose(self, query: str) -> tuple[str, ...]:
        """Decompose a query into subqueries, bounding the output count."""
        try:
            response = await self.llm.generate(self._decompose_prompt, query)
            lines = [line.strip() for line in response.splitlines() if line.strip()]
            return tuple(lines[:self.max_subqueries]) if lines else (query,)
        except Exception:
            # Fallback for decomposition failure is the original query
            return (query,)
