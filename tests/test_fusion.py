from src.retrieval.fusion import reciprocal_rank_fusion

def test_reciprocal_rank_fusion():
    lexical = (
        ("c1", 0.9),
        ("c2", 0.5),
        ("c3", 0.2),
    )
    dense = (
        ("c2", 0.95),
        ("c4", 0.8),
        ("c1", 0.7),
    )
    
    # rank 1 for c1 (lex) and c2 (den)
    # rank 2 for c2 (lex) and c4 (den)
    # rank 3 for c3 (lex) and c1 (den)
    
    fused = reciprocal_rank_fusion(lexical, dense, k=60)
    
    assert len(fused) == 4
    
    c1_score = 1.0 / (60 + 1) + 1.0 / (60 + 3)
    c2_score = 1.0 / (60 + 2) + 1.0 / (60 + 1)
    
    assert fused["c2"][1] == c2_score
    assert fused["c1"][1] == c1_score
    
    # c2 > c1
    assert fused["c2"][0] == 1
    assert fused["c1"][0] == 2
