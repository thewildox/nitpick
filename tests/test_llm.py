from app.analysis.llm import build_snippet


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