from __future__ import annotations

import pytest

from tutor.math_checker import _fmt, _normalize, _safe_eval, check_student_claim


class TestSafeEval:
    def test_basic_division(self):
        assert _safe_eval("100 / 4") == 25.0

    def test_basic_multiplication(self):
        assert _safe_eval("12 * 8") == 96.0

    def test_addition(self):
        assert _safe_eval("15 + 7") == 22.0

    def test_subtraction(self):
        assert _safe_eval("20 - 3") == 17.0

    def test_order_of_operations(self):
        assert _safe_eval("2 + 3 * 4") == 14.0

    def test_parentheses(self):
        assert _safe_eval("(2 + 3) * 4") == 20.0

    def test_caret_as_power(self):
        assert _safe_eval("2^3") == 8.0

    def test_float_result(self):
        assert _safe_eval("7 / 2") == 3.5

    def test_invalid_expression_returns_none(self):
        assert _safe_eval("hello") is None

    def test_empty_string_returns_none(self):
        assert _safe_eval("") is None

    def test_blocked_builtins(self):
        # Malicious input must not execute
        assert _safe_eval("__import__('os').system('echo hi')") is None


class TestNormalize:
    def test_times(self):
        assert "12 * 8" in _normalize("12 times 8")

    def test_divided_by(self):
        assert "100 / 4" in _normalize("100 divided by 4")

    def test_plus(self):
        assert "3 + 4" in _normalize("3 plus 4")

    def test_minus(self):
        assert "10 - 3" in _normalize("10 minus 3")

    def test_case_insensitive(self):
        assert "*" in _normalize("12 TIMES 8")

    def test_no_word_ops(self):
        assert _normalize("100 / 4 = 25") == "100 / 4 = 25"


class TestFmt:
    def test_whole_number(self):
        assert _fmt(25.0) == "25"

    def test_float(self):
        assert _fmt(3.5) == "3.5"

    def test_negative_whole(self):
        assert _fmt(-4.0) == "-4"


class TestCheckStudentClaim:
    # ── Correct answers ──────────────────────────────────────────────────────
    def test_correct_division(self):
        result = check_student_claim("100 / 4 = 25")
        assert result is not None
        assert "CORRECT" in result

    def test_correct_multiplication(self):
        result = check_student_claim("12 * 8 = 96")
        assert result is not None
        assert "CORRECT" in result

    def test_correct_word_times(self):
        result = check_student_claim("12 times 8 = 96")
        assert result is not None
        assert "CORRECT" in result

    def test_correct_word_divided_by(self):
        result = check_student_claim("50 divided by 2 = 25")
        assert result is not None
        assert "CORRECT" in result

    def test_correct_addition(self):
        result = check_student_claim("15 + 7 = 22")
        assert result is not None
        assert "CORRECT" in result

    def test_correct_subtraction(self):
        result = check_student_claim("20 - 3 = 17")
        assert result is not None
        assert "CORRECT" in result

    # ── Wrong answers ─────────────────────────────────────────────────────────
    def test_wrong_division(self):
        result = check_student_claim("100 / 4 = 20")
        assert result is not None
        assert "WRONG" in result
        assert "25" in result

    def test_wrong_multiplication(self):
        result = check_student_claim("12 * 8 = 90")
        assert result is not None
        assert "WRONG" in result
        assert "96" in result

    def test_wrong_word_times(self):
        result = check_student_claim("I think 12 times 8 = 90")
        assert result is not None
        assert "WRONG" in result

    def test_wrong_addition(self):
        result = check_student_claim("3 + 4 = 8")
        assert result is not None
        assert "WRONG" in result
        assert "7" in result

    # ── No claim ─────────────────────────────────────────────────────────────
    def test_no_claim_plain_question(self):
        assert check_student_claim("What is 12 times 8?") is None

    def test_no_claim_i_dont_know(self):
        assert check_student_claim("I don't know where to start") is None

    def test_no_claim_empty(self):
        assert check_student_claim("") is None

    def test_no_claim_single_number(self):
        # "= 25" alone has no LHS operator — should not match
        assert check_student_claim("the answer is 25") is None

    # ── Edge cases ────────────────────────────────────────────────────────────
    def test_float_correct(self):
        result = check_student_claim("7 / 2 = 3.5")
        assert result is not None
        assert "CORRECT" in result

    def test_float_wrong(self):
        result = check_student_claim("7 / 2 = 4")
        assert result is not None
        assert "WRONG" in result

    def test_sentence_with_correct_equation(self):
        result = check_student_claim("I calculated it and 100 / 4 = 25")
        assert result is not None
        assert "CORRECT" in result
