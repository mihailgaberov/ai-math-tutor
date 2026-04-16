from __future__ import annotations

import os
import re

import ollama
from dotenv import load_dotenv

from tutor.math_checker import check_student_claim
from tutor.prompts import SYSTEM_PROMPT

load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MIN_TURNS = int(os.getenv("MIN_TURNS_BEFORE_ANSWER", "3"))

# Patterns that suggest the model accidentally revealed a direct answer too early.
_ANSWER_LEAK_PATTERNS = [
    r"the answer is\s+[\d\w]",
    r"equals\s+[\d]+",
    r"= [\d]+\s*$",
    r"so it'?s\s+[\d]+",
    r"result is\s+[\d]+",
]


def _looks_like_answer_leak(text: str, turn: int) -> bool:
    """Return True if the reply seems to give away the answer before the student has tried."""
    if turn >= MIN_TURNS:
        return False
    lower = text.lower()
    return any(re.search(p, lower) for p in _ANSWER_LEAK_PATTERNS)


def _build_messages(history: list[dict], math_note: str | None = None) -> list[dict]:
    """Prepend the system prompt and an optional math-check note to the history."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if math_note:
        messages.append({"role": "system", "content": math_note})
    messages.extend(history)
    return messages


def chat(history: list[dict]) -> str:
    """
    Send the conversation history to Ollama and return the assistant reply.
    history: list of {"role": "user"|"assistant", "content": str}
    """
    client = ollama.Client(host=HOST)
    turn = sum(1 for m in history if m["role"] == "user")

    last_user_msg = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
    math_note = check_student_claim(last_user_msg)

    response = client.chat(
        model=MODEL,
        messages=_build_messages(history, math_note),
    )
    reply = response["message"]["content"]

    if _looks_like_answer_leak(reply, turn):
        reply = (
            "Hmm, let me rephrase that! 😊 Instead of telling you the answer, "
            "let me ask you this: what do you think the very first step should be? "
            "Take your time — there's no rush!"
        )

    return reply


def is_ollama_running() -> bool:
    """Check if the Ollama server is reachable."""
    try:
        client = ollama.Client(host=HOST)
        client.list()
        return True
    except Exception:
        return False


def model_is_available() -> bool:
    """Check if the configured model has been pulled."""
    try:
        client = ollama.Client(host=HOST)
        models = client.list()
        names = [m["model"] for m in models.get("models", [])]
        return any(MODEL in n for n in names)
    except Exception:
        return False
