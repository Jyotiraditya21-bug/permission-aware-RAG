# Permission-aware adaptive knowledge search

## Problem and outcome
Employees need grounded answers across internal docs, tickets, and wikis without exposing content they cannot access. Deliver an async search-and-answer API that retrieves permitted evidence, adapts retrieval to the query, and cites source chunk IDs.

## Users and scope
Employees ask questions using their authenticated identity and current permissions. Knowledge maintainers ingest and update source content and access metadata. Evaluators measure retrieval quality independently from answer grounding. The initial scope is text ingestion, retrieval, answers, citations, caching, and evaluation; a frontend, source write-back, and provider-specific integrations are outside this design.

## Required behavior
- Route each query to `decompose`, `direct-retrieve`, or `no-retrieval-needed`. Decomposed queries use the same access scope for every subquery. Only non-factual conversational responses may bypass retrieval; requests for internal facts require evidence.
- Resolve trusted user/group access metadata before retrieval. Apply tenant and ACL predicates inside both BM25 and dense queries, before candidates or scores are returned. Missing or unresolvable permissions fail closed.
- Fuse lexical and embedding candidates, deduplicate by chunk ID, then rerank permitted evidence. Return a grounded answer with claim-level source chunk IDs, or abstain when evidence is insufficient.
- Detect source changes using hashes and modification metadata; re-index changed content only. Handle deletions and ACL-only changes without leaving stale content or access available.
- Reuse answers for semantically equivalent paraphrases by query-embedding similarity, not exact text matching, only within a current, compatible permission scope and corpus/configuration version. Cache hits must preserve grounding and citations; tune similarity thresholds against evaluation data.
- Record recall@k and MRR as retrieval metrics and faithfulness as a separate generation metric; never combine them into one score or event namespace.

## Acceptance and release gates
Automated tests demonstrate all three routes, hybrid fusion and reranking, unchanged-document skips, content/ACL/deletion updates, semantic cache hits/misses and invalidation, and citation validation. Adversarial tests show no unauthorized chunk reaches a candidate list, reranker, cache response, generator, citation, or log. A versioned evaluation set reports recall@k, MRR, and faithfulness separately. Quality, latency, cost targets, providers, and cache thresholds remain release decisions to be agreed from baseline results; no dependencies are added without approval.

## Constraints
Python 3.12, typed code, Pydantic v2, async FastAPI; prompts live in `src/prompts/*.md`. Every implemented function gets tests, with LLM and embedding calls mocked in unit tests.
