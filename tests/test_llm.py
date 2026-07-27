from app.analysis.llm import build_snippet
from unittest.mock import patch, MagicMock
from app.analysis.llm import review_snippet


def test_build_snippet_basic():
    content = "\n".join(f"line {i}" for i in range(1, 11))
    result = build_snippet(content, {5})
    assert "   5>| line 5" in result
    assert "   4 | line 4" in result

def test_build_snippet_context_window():
    content = "\n".join(f"line {i}" for i in range(1, 11))
    result = build_snippet(content, {5})
    # context is 3 either side, so lines 2 and 8 appear, line 1 and 9 do not
    assert "line 2" in result
    assert "line 9" not in result


def test_build_snippet_near_top():
    content = "\n".join(f"line {i}" for i in range(1, 11))
    result = build_snippet(content, {1})
    # window wants lines -2 to 4, but negatives don't exist — should not crash
    assert "   1>| line 1" in result


def test_review_snippet_parses_findings():
    fake_response = MagicMock()
    fake_response.stop_reason = "end_turn"
    fake_text = MagicMock()
    fake_text.type = "text"
    fake_text.text = '{"findings": [{"line": 4, "severity": "error", "message": "bug"}]}'
    fake_response.content = [fake_text]

    with patch("app.analysis.llm.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = fake_response
        result = review_snippet("dummy snippet", "test.py")

    assert result == [{"line": 4, "severity": "error", "message": "bug"}]


def test_review_snippet_refusal_returns_empty():
    fake_response = MagicMock()
    fake_response.stop_reason = "refusal"
    fake_text = MagicMock()
    fake_text.type = "text"
    fake_text.text = '{"findings": [{"line": 4, "severity": "error", "message": "bug"}]}'
    fake_response.content = [fake_text]

    with patch("app.analysis.llm.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = fake_response
        result = review_snippet("dummy snippet", "test.py")

    assert result == []