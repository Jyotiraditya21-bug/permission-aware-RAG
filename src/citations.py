"""Citation validation to ensure reference integrity against authorized evidence."""
from typing import Sequence
from src.models import Citation, RetrievalResult

def validate_citations(
    citations: Sequence[Citation], 
    evidence: Sequence[RetrievalResult]
) -> tuple[Citation, ...]:
    """Validate that every cited chunk ID exists in the provided evidence.
    
    If any citation references an unknown or unauthorized chunk ID, the 
    citation is dropped. If dropping citations leaves a claim unsupported,
    the claim is dropped.
    
    Returns a tuple of valid citations.
    """
    valid_ids = {e.chunk_id for e in evidence}
    valid_citations = []
    
    for citation in citations:
        valid_chunk_ids = tuple(
            chunk_id for chunk_id in citation.chunk_ids 
            if chunk_id in valid_ids
        )
        if valid_chunk_ids:
            valid_citations.append(
                Citation(claim=citation.claim, chunk_ids=valid_chunk_ids)
            )
            
    return tuple(valid_citations)
