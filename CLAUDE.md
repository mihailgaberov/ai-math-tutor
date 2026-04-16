# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AI-powered math tutoring application. Python-based, with Ruff used for linting (`.ruff_cache/` is gitignored).

## Commands

Once the project structure is established, populate this section with:

- **Install dependencies**: e.g. `pip install -e ".[dev]"` or `uv sync`
- **Run the app**: e.g. `python -m ai_math_tutor` or `uvicorn app.main:app --reload`
- **Lint**: `ruff check .` and `ruff format --check .`
- **Tests**: `.venv/bin/python -m pytest tests/ -v` or `…pytest tests/test_chat.py::TestChat::test_returns_model_reply` for a single test
- **Type check**: `mypy .` (if mypy is added)

> Update this section when `pyproject.toml`, `requirements.txt`, or equivalent is added.

## Architecture

> This section should be filled in once the codebase is scaffolded. Key areas to document:
> - Entry point(s) and how the app starts
> - How the Claude/AI API is integrated (model, tool use, prompt structure)
> - How math problems are parsed, validated, and evaluated
> - Session/conversation state management
> - Any frontend or API layer (CLI, web, etc.)
