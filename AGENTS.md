# AGENTS.md

PROJECT: Permission-Aware Adaptive RAG Platform — internal knowledge search over docs, tickets, and wikis, with ACL-filtered hybrid retrieval, query routing, incremental ingestion, semantic caching, and citation-grounded generation.

## Read before every task
- Read ARCHITECTURE.md, TASKS.md, and CONTEXT.md before starting any task.
- Do ONLY the task named. No extra features, no refactors, no "while I'm here" changes.

## Stack
- Python 3.12, type hints everywhere, Pydantic v2 for all inputs/outputs.
- Async FastAPI for the API layer.
- Prompts live in src/prompts/*.md files — never inline strings in code.
- All config and secrets via environment variables (pydantic-settings). Never hardcode secrets.

## Approved dependencies (add without asking)
pydantic>=2,<3, fastapi, uvicorn, pydantic-settings, chromadb, rank-bm25,
sentence-transformers, cross-encoder, httpx, python-multipart, tenacity

Any dependency outside this list: ask first, in one line, before adding it.

## Security-critical rules (non-negotiable, always ask if unsure)
- ACL filtering happens BEFORE retrieval (filter at query time via metadata), never as a post-filter on results.
- ACL default is deny: missing metadata, unknown principal, or unknown attribute = deny access. Fail closed, never fail open.
- Never log or cache full document content alongside a different user's session without re-checking ACL on cache hit.
- Retrieval metrics and generation metrics are tracked and reported SEPARATELY, never merged into one score.

## When to ask vs. when to decide
- Ask ONE short question only when a decision is irreversible, security-relevant (ACL, auth, data access), or changes the architecture.
- For everything else (naming, minor schema shape, validation style, formatting, which standard library helper to use): pick the conventional/standard choice yourself. Do not ask.
- When you do proceed on a judgment call, write it as `ASSUMPTION: <what you chose and why>` in CONTEXT.md. Do not block waiting for confirmation unless it is security-critical.

## Execution behavior
- When given a range of tasks (e.g. "do Task 3 through 8"), complete them in order without stopping for confirmation between tasks, except for security-critical decisions above.
- After each task: write code + tests, run tests, fix failures yourself, then update CONTEXT.md (max 3 lines: what was done, key assumption if any, what's next).
- Every function gets a test. Mock LLM calls and embedding calls in unit tests — never hit real APIs in unit tests.

## Output format
- Output changed/new files only, diff style.
- No long explanations, no restating what you did in prose — CONTEXT.md is the log, not the chat reply.
- One line summary at the end of your output, nothing more.

## Testing & quality
- pytest for all tests. Ruff for linting. Mypy-clean type hints.
- Every new endpoint gets a test for both allowed and denied ACL cases.
- Every retrieval change gets a check that recall/precision assumptions aren't silently broken.