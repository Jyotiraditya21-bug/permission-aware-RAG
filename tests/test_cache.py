import time
from src.cache import SemanticCache
from src.models import AccessScope, Answer, Citation, RetrievalResult, Version

def test_cache_hit_with_compatible_scope_and_evidence():
    cache = SemanticCache(similarity_threshold=0.9)
    scope = AccessScope(tenant_id="t1", principal_id="u1", group_ids=frozenset(), source_policy_attributes={}, permission_epoch=1)
    
    ans = Answer(
        status="grounded",
        text="The sky is blue",
        citations=(Citation(claim="blue", chunk_ids=("c1",)),),
        route="direct-retrieve",
        trace_id="t1"
    )
    
    ev = RetrievalResult(chunk_id="c1", text="blue sky", version=Version(document_version="v", corpus_version="v", acl_version="v"), fusion_rank=1)
    
    cache.put("what color is the sky?", (1.0, 0.0), scope, "v1", ans, [ev])
    
    # Exact hit
    hit = cache.get((1.0, 0.0), scope, "v1", [ev], "direct-retrieve")
    assert hit is not None
    assert hit.text == "The sky is blue"

def test_cache_miss_on_different_scope():
    cache = SemanticCache(similarity_threshold=0.9)
    scope1 = AccessScope(tenant_id="t1", principal_id="u1", group_ids=frozenset(), source_policy_attributes={}, permission_epoch=1)
    scope2 = AccessScope(tenant_id="t1", principal_id="u2", group_ids=frozenset(), source_policy_attributes={}, permission_epoch=1)
    
    ans = Answer(status="grounded", text="secret", citations=(Citation(claim="x", chunk_ids=("c1",)),), route="direct-retrieve", trace_id="t1")
    ev = RetrievalResult(chunk_id="c1", text="secret text", version=Version(document_version="v", corpus_version="v", acl_version="v"), fusion_rank=1)
    
    cache.put("query", (1.0, 0.0), scope1, "v1", ans, [ev])
    
    hit = cache.get((1.0, 0.0), scope2, "v1", [ev], "direct-retrieve")
    assert hit is None

def test_cache_miss_on_missing_evidence():
    cache = SemanticCache(similarity_threshold=0.9)
    scope = AccessScope(tenant_id="t1", principal_id="u1", group_ids=frozenset(), source_policy_attributes={}, permission_epoch=1)
    
    ans = Answer(status="grounded", text="secret", citations=(Citation(claim="x", chunk_ids=("c1",)),), route="direct-retrieve", trace_id="t1")
    ev1 = RetrievalResult(chunk_id="c1", text="secret text", version=Version(document_version="v", corpus_version="v", acl_version="v"), fusion_rank=1)
    ev2 = RetrievalResult(chunk_id="c2", text="other text", version=Version(document_version="v", corpus_version="v", acl_version="v"), fusion_rank=1)
    
    cache.put("query", (1.0, 0.0), scope, "v1", ans, [ev1])
    
    # query evidence lacks c1
    hit = cache.get((1.0, 0.0), scope, "v1", [ev2], "direct-retrieve")
    assert hit is None

def test_cache_expiration():
    cache = SemanticCache(similarity_threshold=0.9)
    scope = AccessScope(tenant_id="t1", principal_id="u1", group_ids=frozenset(), source_policy_attributes={}, permission_epoch=1)
    ans = Answer(status="grounded", text="temp", citations=(Citation(claim="x", chunk_ids=("c1",)),), route="direct-retrieve", trace_id="t1")
    ev = RetrievalResult(chunk_id="c1", text="x", version=Version(document_version="v", corpus_version="v", acl_version="v"), fusion_rank=1)
    
    cache.put("query", (1.0, 0.0), scope, "v1", ans, [ev], ttl_sec=-1)
    
    hit = cache.get((1.0, 0.0), scope, "v1", [ev], "direct-retrieve")
    assert hit is None
