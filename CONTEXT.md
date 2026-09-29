Task 1 complete: declared Python >=3.12 and approved pydantic>=2,<3; added typed request, access, source, chunk, version, retrieval, answer, and settings contracts.
Validation: all 15 unittest tests pass on Python 3.12.5 with Pydantic 2.13.4; tuning values remain explicit, with no provider or release-threshold defaults.
Next: Task 2, trusted identity and query-time ACL scope; contract validation alone does not authorize retrieval or verify evidence support.
Task 1 verified: contracts retained; environment-backed settings and Python 3.12 pytest tooling added; 15 tests pass.
ASSUMPTION: isolated uv workspace avoids unrelated parent projects; runtime providers will offer a deterministic offline baseline and optional HTTP models.
Next: trusted identity and ACL scope.
Task 2 complete: trusted credentials, epoch replacement/revocation, tenant/grant/attribute predicates; 17 tests pass.
ASSUMPTION: explicit empty policy maps impose no attributes; a declared attribute without matching trusted values denies access. Credentials are provisioned out of band.
Next: source normalization.
Task 3 complete: validated docs/tickets/wikis batches, source boundaries, change tokens, deletion and snapshot signals; 19 tests pass.
ASSUMPTION: connectors supply normalized JSON exports; content hashes are recomputed rather than trusting modification timestamps.
Next: incremental state and chunking.
Task 4 complete: stable chunk IDs, recomputed hashes, no-op retries, ACL-only embedding reuse, deletion and vector validation; 22 tests pass.
ASSUMPTION: word-bounded deterministic chunks and content hashes are the conservative baseline; modification tokens never bypass hashing.
Next: filtered indexes and atomic durable publication.
Task 5 complete: lexical (BM25) and dense index adapters enforce ACL/visibility predicates pre-retrieval; staged dual-index publication handles failures, revocations, and deletions atomically; 27 tests pass.
ASSUMPTION: In-memory dense and lexical adapters are sufficient for offline baseline and enforce exact pre-filtering rules.
Next: query router and decomposition.
Task 6 complete: routing defaults to direct-retrieve on ambiguity/failure, bounding subqueries and preserving safety guarantees; 31 tests pass.
ASSUMPTION: Generative LLM interfaces accept simple string prompts without chat templates for internal NLP tasks.
Next: hybrid retrieval and fusion.
Task 7 complete: hybrid search executes filtered subqueries across index types; reciprocal rank fusion correctly deduplicates and ranks results; 33 tests pass.
ASSUMPTION: Missing embedder responses cause query failure rather than silent empty subqueries to avoid degrading quality unnoticed.
Next: reranking and evidence budget.
Task 8 complete: reranking bounds evidence sets and deterministically falls back to fusion rank on failure; 36 tests pass.
ASSUMPTION: Reranker interface is abstracted over potentially batched external provider calls.
Next: semantic answer cache.
Task 9 complete: semantic answer cache enforces exact scope/corpus compatibility and requires evidence grounding to persist hits; 40 tests pass.
ASSUMPTION: Negative caches (re-running known misses) or conversational hits are excluded to prevent unbounded growth without clear recall value.
Next: grounded generation and citations.
Task 10 complete: valid citations strictly reference authorized evidence; invalid/missing grounding causes abstention; 45 tests pass.
ASSUMPTION: LLMs output JSON array of claims reliably; prompt strictly instructs to format response as JSON array.
Next: async API orchestration.
Task 11 complete: async FastAPI binds the full pipeline, enforcing scope, rechecking epochs, and rejecting unauthenticated access; 47 tests pass.
ASSUMPTION: FastAPI dependency overrides allow injecting mocked components during API tests without starting heavy backends.
Next: separate metric streams.
Task 12 complete: separated retrieval MRR/recall and generation faithfulness metrics; properly handles abstentions and missing relevance labels; 52 tests pass.
ASSUMPTION: Faithfulness score is evaluated by LLM zero-to-one proportion directly without chunk-by-chunk detailed chains to save latency.
Next: evaluation and security acceptance.
Task 13 complete: evaluations verify separated metric results and end-to-end ACL/cache/revocation gates pass integration tests; 55 tests pass.
ASSUMPTION: Baseline metrics thresholding for release will be handled outside the application code via CI gating.
Next: Ready for production tuning.
