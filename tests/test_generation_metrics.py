import pytest
from src.metrics.generation import Evaluator
from src.models import Answer, Citation

class MockLLM:
    def __init__(self, score):
        self.score = score
    async def generate(self, prompt, text):
        if isinstance(self.score, Exception):
            raise self.score
        return str(self.score)

@pytest.mark.asyncio
async def test_evaluate_faithfulness():
    llm = MockLLM(0.8)
    evaluator = Evaluator(llm)
    
    ans = Answer(
        status="grounded",
        text="abc",
        citations=(Citation(claim="abc", chunk_ids=("c1",)),),
        route="direct-retrieve",
        trace_id="t1"
    )
    
    m = await evaluator.evaluate_faithfulness(ans)
    assert m.faithfulness_score == 0.8
    assert m.citation_count == 1

@pytest.mark.asyncio
async def test_evaluate_faithfulness_abstained():
    llm = MockLLM(1.0)
    evaluator = Evaluator(llm)
    
    ans = Answer(
        status="abstained",
        text="abc",
        citations=(),
        route="direct-retrieve",
        trace_id="t1"
    )
    
    m = await evaluator.evaluate_faithfulness(ans)
    assert m.faithfulness_score is None
    assert m.citation_count == 0
