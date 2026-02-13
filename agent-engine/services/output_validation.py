import re

AUTH_ERROR_PATTERNS = [
    re.compile(r"authentication_error", re.IGNORECASE),
    re.compile(r"OAuth token has expired", re.IGNORECASE),
    re.compile(r"API Error: 401\b"),
    re.compile(r"Failed to authenticate"),
    re.compile(r"invalid.*api.?key", re.IGNORECASE),
    re.compile(r"unauthorized", re.IGNORECASE),
]

NARRATION_PATTERNS = [
    re.compile(r"^I'll (?:start by )?follow(?:ing)? the [Dd]iscovery [Pp]rotocol.*$", re.MULTILINE),
    re.compile(r"^I'll (?:start|begin|process|handle).*$", re.MULTILINE),
    re.compile(r"^I need to (?:understand|check|look|read|analyze|investigate).*$", re.MULTILINE),
    re.compile(r"^Let me .*$", re.MULTILINE),
    re.compile(r"^Now (?:let me|I'll|I need to|I have|I can|that I).*$", re.MULTILINE),
    re.compile(r"^(?:First|Next|Finally),? (?:let me|I'll|I need to).*$", re.MULTILINE),
    re.compile(r"^Looking at (?:the |this ).*$", re.MULTILINE),
    re.compile(r"^Based on (?:my |the ).*$", re.MULTILINE),
    re.compile(r"^\[.*?\]$", re.MULTILINE),
    re.compile(r"^\[TOOL\].*$", re.MULTILINE),
    re.compile(r"^\[TOOL RESULT\].*$", re.MULTILINE),
    re.compile(r"^\[TOOL ERROR\].*$", re.MULTILINE),
    re.compile(r"^\[LOG\].*$", re.MULTILINE),
    re.compile(r"^\[CLI\].*$", re.MULTILINE),
    re.compile(r"^\*\*User\*\*:.*$", re.MULTILINE),
    re.compile(r"^.*(?:Reading|Loading) (?:manifest|agent|skill).*$", re.MULTILINE),
]

TOOL_OUTPUT_BLOCK = re.compile(
    r"\[TOOL\].*?\[TOOL RESULT\].*?(?=\n\n|\n\[TOOL\]|\Z)",
    re.DOTALL,
)

FINAL_RESPONSE_MARKER = "<!-- FINAL_RESPONSE -->"


def detect_auth_failure(output: str) -> str | None:
    for pattern in AUTH_ERROR_PATTERNS:
        match = pattern.search(output)
        if match:
            return match.group(0)
    return None


def extract_final_response(output: str) -> str | None:
    if FINAL_RESPONSE_MARKER in output:
        parts = output.split(FINAL_RESPONSE_MARKER)
        if len(parts) >= 2:
            return parts[-1].strip()
    return None


def clean_agent_output(output: str) -> str:
    if not output:
        return output

    final = extract_final_response(output)
    if final:
        return final

    cleaned = TOOL_OUTPUT_BLOCK.sub("", output)

    for pattern in NARRATION_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    lines = cleaned.split("\n")
    cleaned_lines = [line for line in lines if line.strip()]
    return "\n".join(cleaned_lines).strip()
