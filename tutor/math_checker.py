from __future__ import annotations

import math
import re

_SAFE_GLOBALS = {"__builtins__": {}}
_SAFE_LOCALS = {
    "abs": abs, "round": round, "pow": pow,
    "sqrt": math.sqrt, "floor": math.floor, "ceil": math.ceil,
    "pi": math.pi,
}

# Matches "100 / 4 = 20", "12 * 8 = 96" — LHS must contain an operator
_EQUATION_RE = re.compile(
    r"([\d\s\.]*[\+\-\*\/][\d\s\.\+\-\*\/\(\)]*)\s*=\s*([\-\d\.]+)"
)

# Word-to-symbol substitutions before parsing
_WORD_OPS = [
    (re.compile(r"\btimes\b", re.IGNORECASE), "*"),
    (re.compile(r"\bdivided\s+by\b", re.IGNORECASE), "/"),
    (re.compile(r"\bplus\b", re.IGNORECASE), "+"),
    (re.compile(r"\bminus\b", re.IGNORECASE), "-"),
]
_ANSWER_CLAIM_RE = re.compile(
    r"(?:answer\s+is|equals|it(?:'?s| is)|result\s+is|=\s*)([\-\d\.]+)",
    re.IGNORECASE,
)


def _safe_eval(expr: str) -> float | None:
    """Evaluate a simple arithmetic expression safely. Returns None on failure."""
    try:
        expr = expr.strip().replace("^", "**")
        result = eval(expr, _SAFE_GLOBALS, _SAFE_LOCALS)  # noqa: S307
        return float(result)
    except Exception:
        return None


def _normalize(text: str) -> str:
    """Replace word operators with symbols."""
    for pattern, symbol in _WORD_OPS:
        text = pattern.sub(symbol, text)
    return text


def check_student_claim(text: str) -> str | None:
    """
    Inspect the student's message for a mathematical claim.
    Returns a verification note to inject into the model context, or None if
    no checkable claim is found.
    """
    text = _normalize(text)
    # Try to find "expression = value" pattern first
    match = _EQUATION_RE.search(text)
    if match:
        lhs, claimed = match.group(1).strip(), match.group(2).strip()
        actual = _safe_eval(lhs)
        if actual is not None:
            try:
                claimed_val = float(claimed)
            except ValueError:
                return None
            correct = abs(actual - claimed_val) < 1e-6
            if correct:
                return f"[MATH CHECK: {lhs} = {claimed_val} — CORRECT ✓]"
            else:
                return (
                    f"[MATH CHECK: The student claims {lhs} = {claimed_val}. "
                    f"Actual result: {_fmt(actual)}. The student is WRONG. "
                    f"Do NOT confirm this. Guide them to discover the correct answer.]"
                )

    return None


def _fmt(value: float) -> str:
    """Format a float cleanly (drop .0 for whole numbers)."""
    return str(int(value)) if value == int(value) else str(round(value, 6))
