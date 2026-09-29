import pytest
from src.indexes.dense import DenseIndex
from src.indexes.lexical import LexicalIndex
from src.models import AccessScope, Chunk, SourceACL
from src.retrieval.hybrid import HybridRetriever

class MockEmbedder:
    async def embed(self, texts):
        return tuple([(1.0, 0.0)] * len(texts))

def make_chunk(chunk_id, text):
    return Chunk(
        chunk_id=chunk_id,
        document_id="d1",
        document_version="v1",
        text=text,
        source_locator="l1",
        tenant_id="t1",
        acl=SourceACL(principal_ids=frozenset(["u1"]), group_ids=frozenset(), source_policy_attributes={}, acl_version="a1"),
    )

@pytest.mark.asyncio
async def test_hybrid_search():
    lex = LexicalIndex()
    den = DenseIndex()
    
    c1 = make_chunk("c1", "test hybrid search")
    c2 = make_chunk("c2", "search query")
    
    lex.publish_version("v1", [(c1, (1.0, 0.0)), (c2, (1.0, 0.0))])
    den.publish_version("v1", [(c1, (1.0, 0.0)), (c2, (1.0, 0.0))])
    
    retriever = HybridRetriever(lex, den, MockEmbedder(), top_k=2)
    scope = AccessScope(tenant_id="t1", principal_id="u1", group_ids=frozenset(), source_policy_attributes={}, permission_epoch=1)
    
    results = await retriever.search(("test",), scope, "v1")
    assert len(results) == 2
    
    res_dict = {r.chunk_id: r for r in results}
    assert res_dict["c1"].lexical_score is not None
    assert res_dict["c1"].dense_score is not None
    assert res_dict["c1"].fusion_rank in (1, 2)
