import pytest
from src.citations import validate_citations
from src.models import Citation, RetrievalResult, Version

def make_result(chunk_id):
    return RetrievalResult(
        chunk_id=chunk_id,
        text="text",
        version=Version(document_version="v", corpus_version="v", acl_version="v"),
        fusion_rank=1
    )

def test_validate_citations():
    ev = [make_result("c1"), make_result("c2")]
    
    citations = [
        Citation(claim="Valid", chunk_ids=("c1",)),
        Citation(claim="Partial", chunk_ids=("c1", "c3")),
        Citation(claim="Invalid", chunk_ids=("c3", "c4")),
    ]
    
    valid = validate_citations(citations, ev)
    
    assert len(valid) == 2
    assert valid[0].claim == "Valid"
    assert valid[0].chunk_ids == ("c1",)
    
    assert valid[1].claim == "Partial"
    assert valid[1].chunk_ids == ("c1",)
