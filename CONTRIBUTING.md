# Contributing

Thank you for your interest in the Permission-Aware Adaptive RAG Platform! 

This repository primarily serves as a solo portfolio project and reference architecture for building secure, ACL-filtered Retrieval-Augmented Generation systems. 

While I am not actively seeking large feature contributions, I am always open to discussions, bug reports, and minor improvements.

## How to Contribute

1. **Issues First**: If you spot a bug or have a suggestion, please [open an issue](https://github.com/Jyotiraditya21-bug/permission-aware-RAG/issues) to discuss it before spending time writing code.
2. **Fork and PR**: For typo fixes, minor bug fixes, or documentation improvements, feel free to fork the repository and submit a Pull Request.
3. **Environment Setup**: 
   - We use `uv` for dependency management. Please run `uv pip install -e .` to setup your environment.
   - Code must pass `ruff` validation: `ruff check src/ tests/ evals/`
   - All tests must pass: `pytest -v tests/`

## Project Principles
If you are submitting a PR, please ensure it aligns with the core principles of the project:
- **Security First**: All access controls are applied *before* retrieval. No exceptions.
- **Fail Closed**: Any missing or malformed authentication/authorization context must result in a strict denial of access.
- **Strict Typing**: Use Pydantic v2 and Python 3.12+ type hints rigorously.

Thank you for exploring this architecture!
