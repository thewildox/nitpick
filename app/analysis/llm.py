import json
from app.config import settings
import anthropic

SYSTEM = """You are a senior Python code reviewer for GitHub pull requests.

You receive a snippet from one changed file. Each line is prefixed with its line \
number in the form "  42 | <code>". Lines the pull request actually changed are \
marked with ">" after the number; unmarked lines are surrounding context, shown \
only to help you understand the change.

Deterministic tools already run on this code: Ruff (linting/style) and Bandit \
(security). Do NOT report anything they would catch — style, formatting, import \
order, naming, or known lint/security rules. Review only what they cannot judge:
- logic errors and likely bugs (off-by-one, wrong operator, inverted condition)
- unhandled edge cases (empty input, None, zero, boundary values)
- unsafe assumptions (unchecked indexing, missing error handling at boundaries)
- concurrency, resource, or state-management mistakes
- design that is unclear or that will cause bugs to be introduced later

Report findings ONLY on lines marked with ">". Never report on context lines, \
and never report a line number that does not appear in the snippet. Assign severity:
- "error": a bug that will cause incorrect behavior, a crash, or a security hole
- "warning": a likely problem or risky pattern worth fixing before merge
- "info": a minor concern or suggestion

Keep each message to one or two sentences: what is wrong and why it matters. \
Report every genuine issue you find; if the code is correct and clear, return no \
findings. Do not invent problems to fill the list."""


def build_snippet(content: str, changed: set[int], context: int = 3) -> str:
    lines = content.splitlines()

    keep = set()
    for line_no in changed:
        for offset in range(-context, context + 1):
            keep.add(line_no + offset)

    out = []
    for i, text in enumerate(lines, start=1):
        if i not in keep:
            continue
        marker = ">" if i in changed else " "
        out.append(f"{i:4d}{marker}| {text}")

    return "\n".join(out)


def review_snippet(snippet: str, filename: str) -> list[dict]:
    """Send the snippet to Claude, return parsed findings.
    Each dict: {"line": int, "severity": str, "message": str}"""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    schema = {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "line": {"type": "integer"},
                            "severity": {
                                "type": "string",
                                "enum": ["error", "warning", "info"],
                            },
                            "message": {"type": "string"},
                        },
                        "required": ["line", "severity", "message"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["findings"],
            "additionalProperties": False,
        }

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=8192,
        thinking={"type": "adaptive"},
        system=SYSTEM,
        output_config={"format": {"type": "json_schema", "schema": schema}},
        messages=[
            {"role": "user", "content": f"File: {filename}\n\n{snippet}"},
        ],
    )

    # A safety refusal yields no usable JSON; treat it as "nothing to report".
    if response.stop_reason == "refusal":
        return []

    # With thinking on, the response also carries thinking blocks; the schema-
    # constrained JSON lives in the text block.
    text = next(block.text for block in response.content if block.type == "text")
    return json.loads(text)["findings"]