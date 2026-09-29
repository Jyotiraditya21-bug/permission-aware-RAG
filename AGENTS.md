# AGENTS.md
PROJECT: Permission-aware adaptive RAG platform over docs/tickets/wikis.

- Read ARCHITECTURE.md, TASKS.md, CONTEXT.md before every task.
- Do ONLY the named task. No extra features, no refactors.
- Python 3.12, type hints, Pydantic v2, async FastAPI.
- Prompts in src/prompts/*.md, never inline strings.
- ACL check happens BEFORE retrieval, not after (filter at query time, not post-filter results).
- Retrieval and generation metrics are logged separately, never merged.
- No new dependency without asking first.
- Every function gets a test. Mock LLM/embedding calls in unit tests.
- Output: changed files only, diff style. No explanations unless asked.
- Update CONTEXT.md (max 3 lines) after each task.
- If unsure, ask 1 question. Never guess.
- Approved dependencies (add without asking): pydantic>=2,<3, fastapi, uvicorn, chromadb, rank-bm25, sentence-transformers, cross-encoder.
