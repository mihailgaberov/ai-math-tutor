---
title: Maximo — AI Math Tutor
emoji: 🧮
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: 1.56.0
app_file: app.py
pinned: false
---

# 🧮 Maximo — AI Math Tutor

A local AI math tutor for kids aged **8–14**. Maximo is a friendly persona that guides students through math problems using the **Socratic method** — never giving away direct answers, only nudges — so children build real understanding rather than copying solutions.

Runs fully offline via [Ollama](https://ollama.com). No data leaves the machine.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.35%2B-red)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **Socratic tutoring** — Maximo breaks problems into steps and asks guiding questions instead of revealing answers
- **Answer-leak guardrail** — a post-call interceptor catches accidental answer leaks from the model on early turns
- **Python-verified arithmetic** — student claims like `12 * 8 = 96` are evaluated by Python, not the LLM, so the model can never confirm a wrong answer
- **Fully offline** — powered by [Ollama](https://ollama.com) with `qwen2.5:3b` (≈2 GB, one-time download)
- **Zero login / zero tracking** — each browser session is a fresh, ephemeral conversation
- **Configurable** — model, host, and tutoring patience all adjustable via `.env`

---

## Demo

```
Student: what is 144 / 12?
Maximo:  Ooh, good problem! Let's think about this together. 🤔
         What do you think division means — can you describe it in your own words?

Student: it means splitting into groups
Maximo:  Great thinking! So if we split 144 into 12 equal groups,
         how many would be in each group? What's your first guess?

Student: I think it's 12
Maximo:  Nice try! You're so close. 😊 Let me ask you this:
         what is 12 × 12? Does that match 144?
```

---

## Architecture

```
user types message
  → app.py           appends to st.session_state.messages
  → tutor/chat.py    extracts last user message
  → math_checker.py  detects any "X op Y = Z" claim, evaluates with Python
  → chat.py          injects math verification note as hidden system message
  → Ollama API       receives [system_prompt] + [math_note?] + [conversation history]
  → chat.py          intercepts answer leaks on early turns (< MIN_TURNS_BEFORE_ANSWER)
  → app.py           renders reply, appends to history
```

### Key modules

| File | Responsibility |
|---|---|
| `app.py` | Streamlit entry point — session state, health-check UI, sidebar, chat rendering |
| `tutor/chat.py` | Core logic — builds message list, calls Ollama, runs leak interceptor |
| `tutor/math_checker.py` | Python-evaluated arithmetic checker — normalises word operators, sandboxed `eval` |
| `tutor/prompts.py` | `SYSTEM_PROMPT` defining Maximo's persona, Socratic rules, and tone |

### Why Python checks the math

Small models (3 B parameters) can confidently confirm wrong arithmetic. `math_checker.py` intercepts every student claim of the form `LHS = value`, evaluates `LHS` with Python, and injects a `[MATH CHECK: ...]` note into the model context before the API call. The LLM never decides whether the student's arithmetic is correct — Python does.

---

## Requirements

- Python 3.9+
- [Ollama](https://ollama.com) (installed automatically by `start.sh` on macOS)
- ~2 GB disk space for the `qwen2.5:3b` model

---

## Quick start

```bash
git clone https://github.com/your-username/ai-math-tutor
cd ai-math-tutor
./start.sh
```

`start.sh` will:
1. Install Ollama (macOS via Homebrew) if missing
2. Start the Ollama server if not running
3. Pull `qwen2.5:3b` on first run (~2 GB)
4. Create a `.venv` and install Python dependencies
5. Copy `.env.example` → `.env`
6. Open the app at **http://localhost:8501**

### Manual setup

```bash
python3 -m venv .venv
.venv/bin/pip install streamlit ollama python-dotenv
cp .env.example .env
ollama serve &
ollama pull qwen2.5:3b
.venv/bin/streamlit run app.py
```

---

## Configuration

Copy `.env.example` to `.env` and edit as needed:

```ini
OLLAMA_MODEL=qwen2.5:3b        # any model available in Ollama
OLLAMA_HOST=http://localhost:11434
MIN_TURNS_BEFORE_ANSWER=3      # how many student attempts before Maximo may reveal the answer
```

---

## Development

```bash
# Run tests
.venv/bin/python -m pytest tests/ -v

# Lint
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

The test suite (62 tests) covers chat logic, math checker edge cases, the answer-leak interceptor, and Ollama health checks.

---

## Deploying to Hugging Face Spaces

> **Note:** Hugging Face Spaces does not run Ollama natively. To deploy publicly you have two options:
>
> **Option A — swap the backend** Replace `ollama.Client` in `tutor/chat.py` with the [Anthropic](https://docs.anthropic.com) or [OpenAI](https://platform.openai.com) SDK and set the API key as an HF Space secret.
>
> **Option B — Docker Space** Use a [Docker Space](https://huggingface.co/docs/hub/spaces-sdks-docker) with a `Dockerfile` that installs Ollama and pulls the model at build time (image will be large).

For a quick cloud demo, Option A (swap to a hosted API) is recommended.

---

## License

MIT — see [LICENSE](LICENSE).
