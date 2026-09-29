import json
import pytest
from src.generation import Generator
from src.models import RetrievalResult, Version

class MockLLM:
    def __init__(self, response):
        self.response = response
        
    async def generate(self, prompt, text):
        if isinstance(self.response, Exception):
            raise self.response
        return self.response

def make_result(chunk_id):
    return RetrievalResult(
        chunk_id=chunk_id,
        text="text",
        version=Version(document_version="v", corpus_version="v", acl_version="v"),
        fusion_rank=1
    )

@pytest.mark.asyncio
async def test_generation_grounded():
    llm = MockLLM(json.dumps([{"claim": "True fact.", "chunk_ids": ["c1"]}]))
    gen = Generator(llm)
    
    ev = [make_result("c1")]
    ans = await gen.generate("query", ev, "direct-retrieve")
    
    assert ans.status == "grounded"
    assert ans.text == "True fact."
    assert len(ans.citations) == 1
    assert ans.citations[0].chunk_ids == ("c1",)

@pytest.mark.asyncio
async def test_generation_abstained_on_invalid_citation():
    llm = MockLLM(json.dumps([{"claim": "Fake fact.", "chunk_ids": ["unknown"]}]))
    gen = Generator(llm)
    
    ev = [make_result("c1")]
    ans = await gen.generate("query", ev, "direct-retrieve")
    
    assert ans.status == "abstained"
    assert len(ans.citations) == 0

@pytest.mark.asyncio
async def test_generation_conversational():
    llm = MockLLM("Hello there!")
    gen = Generator(llm)
    
    ans = await gen.generate("hi", [], "no-retrieval-needed")
    
    assert ans.status == "conversational"
    assert ans.text == "Hello there!"
    assert len(ans.citations) == 0

@pytest.mark.asyncio
async def test_generation_abstained_on_llm_failure():
    llm = MockLLM(RuntimeError("fail"))
    gen = Generator(llm)
    
    ans = await gen.generate("query", [make_result("c1")], "direct-retrieve")
    
    assert ans.status == "abstained"
