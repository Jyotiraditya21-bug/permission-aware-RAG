import pytest

from src.router import QueryRouter


class MockLLM:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def generate(self, prompt: str, input_text: str) -> str:
        self.calls.append((prompt, input_text))
        if isinstance(self.responses, Exception):
            raise self.responses
        if isinstance(self.responses, list):
            if not self.responses:
                raise RuntimeError("No more mocked responses")
            return self.responses.pop(0)
        return self.responses


@pytest.mark.asyncio
async def test_route_valid_options():
    llm = MockLLM(["direct-retrieve", "decompose", "no-retrieval-needed"])
    router = QueryRouter(llm)
    
    assert await router.route("q1") == "direct-retrieve"
    assert await router.route("q2") == "decompose"
    assert await router.route("q3") == "no-retrieval-needed"


@pytest.mark.asyncio
async def test_route_fallback_on_invalid_or_error():
    llm = MockLLM(["invalid-route"])
    router = QueryRouter(llm)
    assert await router.route("q1") == "direct-retrieve"
    
    llm_error = MockLLM(RuntimeError("API down"))
    router_error = QueryRouter(llm_error)
    assert await router_error.route("q2") == "direct-retrieve"


@pytest.mark.asyncio
async def test_decompose_bounded():
    llm = MockLLM("sub1\nsub2\nsub3\nsub4")
    router = QueryRouter(llm, max_subqueries=2)
    subqueries = await router.decompose("complex query")
    
    assert len(subqueries) == 2
    assert subqueries == ("sub1", "sub2")


@pytest.mark.asyncio
async def test_decompose_fallback():
    llm_error = MockLLM(RuntimeError("API down"))
    router = QueryRouter(llm_error)
    subqueries = await router.decompose("complex query")
    
    assert len(subqueries) == 1
    assert subqueries == ("complex query",)
