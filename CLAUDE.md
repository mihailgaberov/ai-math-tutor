# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Local AI math tutor for kids (ages 8–14). A Streamlit chat UI where a persona called **Maximo** guides students through math problems using the Socratic method — never revealing direct answers, only nudges. Runs fully offline via Ollama.

## Commands

- **Set up**: `python3 -m venv .venv && .venv/bin/pip install streamlit ollama python-dotenv`
- **Run the app**: `./start.sh` (handles Ollama, model pull, venv, and browser launch) or `.venv/bin/streamlit run app.py`
- **Tests**: `.venv/bin/python -m pytest tests/ -v`
- **Single test**: `.venv/bin/python -m pytest tests/test_chat.py::TestChat::test_returns_model_reply`
- **Lint**: `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .`

The `.venv/` directory is not committed. Python 3.14 (Homebrew) is the active interpreter — do not use the system `python3` directly as it points to an externally-managed Homebrew install.

## Architecture

### Request flow

```
user types message
  → app.py            appends to st.session_state.messages
  → tutor/chat.py     extracts last user message
  → math_checker.py   detects any "X op Y = Z" claim, evaluates with Python
  → chat.py           injects math verification note as hidden system message (if claim found)
  → Ollama API        receives [system_prompt] + [math_note?] + [conversation history]
  → chat.py           intercepts answer leaks on early turns (< MIN_TURNS_BEFORE_ANSWER)
  → app.py            renders reply, appends to history
```

### Key modules

- **`app.py`** — Streamlit entry point. Owns session state (`st.session_state.messages`), health-check UI, sidebar, and chat rendering. Each browser session is a fresh conversation.
- **`tutor/chat.py`** — Core logic. Calls `ollama.Client`, builds the message list, runs the answer-leak interceptor. Two guardrail layers: math verification (pre-call) and leak detection (post-call).
- **`tutor/math_checker.py`** — Python-evaluated arithmetic checker. Normalises word operators ("times" → `*`, "divided by" → `/`), evaluates the LHS with a sandboxed `eval`, and returns a `[MATH CHECK: ...]` note injected into the model context. This is what prevents the small model from confirming wrong answers.
- **`tutor/prompts.py`** — Single `SYSTEM_PROMPT` constant defining Maximo's persona, rules (no direct answer on first turn, Socratic nudges, 3-attempt escalation), and tone.

### AI integration

- Model: `qwen2.5:3b` via Ollama (local, no internet after install). Configurable via `OLLAMA_MODEL` env var.
- No streaming — full response returned before rendering.
- Math correctness is **not** delegated to the LLM. Python checks the arithmetic; the LLM only handles language and pedagogy.

### Configuration (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5:3b` | Model to use |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `MIN_TURNS_BEFORE_ANSWER` | `3` | Turns before the tutor may reveal the answer |

Copy `.env.example` to `.env` to customise — `start.sh` does this automatically on first run.
