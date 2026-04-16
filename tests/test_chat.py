from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tutor.chat import _build_messages, _looks_like_answer_leak, chat, is_ollama_running, model_is_available
from tutor.prompts import SYSTEM_PROMPT


class TestLooksLikeAnswerLeak:
    def test_detects_the_answer_is(self):
        assert _looks_like_answer_leak("The answer is 96", turn=1) is True

    def test_detects_equals_at_end_of_line(self):
        assert _looks_like_answer_leak("So 12 × 8 = 96", turn=1) is True

    def test_detects_result_is(self):
        assert _looks_like_answer_leak("The result is 25!", turn=1) is True

    def test_detects_so_its(self):
        assert _looks_like_answer_leak("So it's 42", turn=1) is True

    def test_detects_equals_pattern(self):
        assert _looks_like_answer_leak("12 times 8 equals 96", turn=1) is True

    def test_nudge_reply_not_flagged(self):
        assert _looks_like_answer_leak("What do you think the first step is?", turn=1) is False

    def test_no_leak_after_min_turns(self):
        # Once MIN_TURNS (3) is reached, the tutor is allowed to reveal the answer
        assert _looks_like_answer_leak("The answer is 96", turn=3) is False

    def test_no_leak_well_past_min_turns(self):
        assert _looks_like_answer_leak("The answer is 96", turn=10) is False


class TestBuildMessages:
    def test_always_starts_with_system_prompt(self):
        messages = _build_messages([])
        assert messages[0] == {"role": "system", "content": SYSTEM_PROMPT}

    def test_history_appended_after_system(self):
        history = [{"role": "user", "content": "What is 2+2?"}]
        messages = _build_messages(history)
        assert messages[-1] == history[0]

    def test_math_note_injected_as_second_system_message(self):
        note = "[MATH CHECK: 2 + 2 = 5 — WRONG]"
        messages = _build_messages([], math_note=note)
        assert messages[1] == {"role": "system", "content": note}

    def test_no_math_note_produces_two_messages(self):
        history = [{"role": "user", "content": "hi"}]
        messages = _build_messages(history, math_note=None)
        assert len(messages) == 2  # system + user

    def test_math_note_produces_three_messages(self):
        history = [{"role": "user", "content": "hi"}]
        messages = _build_messages(history, math_note="[MATH CHECK: ...]")
        assert len(messages) == 3  # system + note + user

    def test_full_conversation_order(self):
        history = [
            {"role": "user", "content": "What is 100/4?"},
            {"role": "assistant", "content": "Good question! What do you think?"},
            {"role": "user", "content": "100 / 4 = 20"},
        ]
        messages = _build_messages(history)
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[-1]["content"] == "100 / 4 = 20"


class TestChat:
    def _make_response(self, content: str) -> dict:
        return {"message": {"content": content}}

    @patch("tutor.chat.ollama.Client")
    def test_returns_model_reply(self, MockClient):
        MockClient.return_value.chat.return_value = self._make_response("What step do you think comes first?")
        history = [{"role": "user", "content": "What is 5 + 3?"}]
        result = chat(history)
        assert result == "What step do you think comes first?"

    @patch("tutor.chat.ollama.Client")
    def test_intercepts_answer_leak_on_turn_1(self, MockClient):
        MockClient.return_value.chat.return_value = self._make_response("The answer is 8")
        history = [{"role": "user", "content": "What is 5 + 3?"}]
        result = chat(history)
        assert "The answer is 8" not in result
        assert "first step" in result.lower()

    @patch("tutor.chat.ollama.Client")
    def test_allows_answer_after_min_turns(self, MockClient):
        MockClient.return_value.chat.return_value = self._make_response("Yes! The answer is 8, well done!")
        history = [
            {"role": "user", "content": "What is 5 + 3?"},
            {"role": "assistant", "content": "What do you think?"},
            {"role": "user", "content": "Is it 8?"},
            {"role": "assistant", "content": "Almost!"},
            {"role": "user", "content": "8?"},
        ]
        result = chat(history)
        assert "The answer is 8" in result

    @patch("tutor.chat.ollama.Client")
    def test_math_note_injected_for_wrong_claim(self, MockClient):
        mock_client = MockClient.return_value
        mock_client.chat.return_value = self._make_response("Not quite! Try again.")
        history = [{"role": "user", "content": "100 / 4 = 20"}]
        chat(history)
        call_messages = mock_client.chat.call_args[1]["messages"]
        system_contents = [m["content"] for m in call_messages if m["role"] == "system"]
        assert any("WRONG" in c for c in system_contents)

    @patch("tutor.chat.ollama.Client")
    def test_math_note_injected_for_correct_claim(self, MockClient):
        mock_client = MockClient.return_value
        mock_client.chat.return_value = self._make_response("Yes! That's right!")
        history = [{"role": "user", "content": "100 / 4 = 25"}]
        chat(history)
        call_messages = mock_client.chat.call_args[1]["messages"]
        system_contents = [m["content"] for m in call_messages if m["role"] == "system"]
        assert any("CORRECT" in c for c in system_contents)

    @patch("tutor.chat.ollama.Client")
    def test_no_math_note_for_plain_question(self, MockClient):
        mock_client = MockClient.return_value
        mock_client.chat.return_value = self._make_response("Great question! What do you think?")
        history = [{"role": "user", "content": "What is 100 divided by 4?"}]
        chat(history)
        call_messages = mock_client.chat.call_args[1]["messages"]
        system_contents = [m["content"] for m in call_messages if m["role"] == "system"]
        assert not any("MATH CHECK" in c for c in system_contents)


class TestHealthChecks:
    @patch("tutor.chat.ollama.Client")
    def test_is_ollama_running_true(self, MockClient):
        MockClient.return_value.list.return_value = {}
        assert is_ollama_running() is True

    @patch("tutor.chat.ollama.Client")
    def test_is_ollama_running_false(self, MockClient):
        MockClient.return_value.list.side_effect = ConnectionError("refused")
        assert is_ollama_running() is False

    @patch("tutor.chat.ollama.Client")
    def test_model_is_available_true(self, MockClient):
        MockClient.return_value.list.return_value = {
            "models": [{"model": "qwen2.5:3b"}]
        }
        assert model_is_available() is True

    @patch("tutor.chat.ollama.Client")
    def test_model_is_available_false_empty_list(self, MockClient):
        MockClient.return_value.list.return_value = {"models": []}
        assert model_is_available() is False

    @patch("tutor.chat.ollama.Client")
    def test_model_is_available_false_on_error(self, MockClient):
        MockClient.return_value.list.side_effect = RuntimeError("down")
        assert model_is_available() is False
