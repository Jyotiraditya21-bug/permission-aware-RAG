"""Grounded generation producing claim citations."""
import json
import uuid
from pathlib import Path
from typing import Sequence

from src.citations import validate_citations
from src.models import Answer, Citation, RetrievalResult, Route
from src.router import LLMClient

PROMPTS_DIR = Path(__file__).parent / "prompts"


class Generator:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm
        self._answer_prompt = (PROMPTS_DIR / "answer.md").read_text()

    async def generate(
        self,
        query: str,
        evidence: Sequence[RetrievalResult],
        route: Route,
    ) -> Answer:
        """Generate a grounded answer based on evidence.
        
        Conversational queries return a conversational response without citations.
        Queries that cannot be answered from evidence return an abstained response.
        """
        trace_id = str(uuid.uuid4())
        
        if route == "no-retrieval-needed":
            try:
                response = await self.llm.generate("Respond conversationally to:", query)
                text = response.strip() or "Hello!"
            except Exception:
                text = "Hello!"
            return Answer(
                status="conversational",
                text=text,
                citations=(),
                route=route,
                trace_id=trace_id,
            )

        # Build evidence context
        evidence_text = "\n\n".join(
            f"Chunk ID: {e.chunk_id}\nContent: {e.text}" for e in evidence
        )
        prompt = self._answer_prompt.replace("{evidence}", evidence_text)
        
        try:
            response = await self.llm.generate(prompt, query)
            claims = json.loads(response)
        except Exception:
            claims = []
            
        raw_citations = []
        for c in claims:
            try:
                raw_citations.append(Citation(claim=c["claim"], chunk_ids=tuple(c["chunk_ids"])))
            except Exception:
                pass
                
        valid_citations = validate_citations(raw_citations, evidence)
        
        if not valid_citations:
            return Answer(
                status="abstained",
                text="I cannot answer this based on the available evidence.",
                citations=(),
                route=route,
                trace_id=trace_id,
            )
            
        text = " ".join(c.claim for c in valid_citations)
        return Answer(
            status="grounded",
            text=text,
            citations=valid_citations,
            route=route,
            trace_id=trace_id,
        )
