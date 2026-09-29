"""Reciprocal rank fusion for deduplication and candidate ranking."""

def reciprocal_rank_fusion(
    *candidate_lists: tuple[tuple[str, float], ...], 
    k: int = 60
) -> dict[str, tuple[int, float]]:
    """Fuse ranked lists using Reciprocal Rank Fusion.
    
    Returns a mapping of chunk_id -> (fusion_rank, fusion_score).
    """
    scores: dict[str, float] = {}
    
    for candidates in candidate_lists:
        for rank, (chunk_id, _) in enumerate(candidates, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + (1.0 / (k + rank))
            
    # Sort by score descending
    sorted_items = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    
    # Return mapping of chunk_id to (rank, score)
    return {
        chunk_id: (rank, score)
        for rank, (chunk_id, score) in enumerate(sorted_items, start=1)
    }
