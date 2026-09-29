"""Generation metrics reporting evidence faithfulness and citation validity."""
from pathlib import Path
from src.models import Answer, Contract
from src.router import LLMClient

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class GenerationMetric(Contract):
    trace_id: str
    status: str
    is_cached: bool
    citation_count: int
    faithfulness_score: float | None


class Evaluator:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm
        self._prompt = (PROMPTS_DIR / "faithfulness.md").read_text()

    async def evaluate_faithfulness(
        self,
        answer: Answer,
        is_cached: bool = False,
    ) -> GenerationMetric:
        if answer.status != "grounded":
            return GenerationMetric(
                trace_id=answer.trace_id,
                status=answer.status,
                is_cached=is_cached,
                citation_count=0,
                faithfulness_score=None,
            )

        claims_text = "\n".join(c.claim for c in answer.citations)
        prompt = self._prompt.replace("{claims}", claims_text)
        
        try:
            res = await self.llm.generate(prompt, "")
            score = float(res.strip())
            score = max(0.0, min(1.0, score))
        except Exception:
            score = None

        return GenerationMetric(
            trace_id=answer.trace_id,
            status=answer.status,
            is_cached=is_cached,
            citation_count=len(answer.citations),
            faithfulness_score=score,
        )
