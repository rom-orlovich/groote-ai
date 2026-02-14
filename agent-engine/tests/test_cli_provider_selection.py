"""Tests that each agent .md file has a model defined in its frontmatter.

Claude Code natively reads the model: field from .claude/agents/*.md
frontmatter when spawning subagents. These tests verify the frontmatter
is correctly configured so the CLI handles model selection automatically.
"""

import re
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "agents"

EXPECTED_MODELS = {
    "brain": "opus",
    "planning": "opus",
    "github-pr-review": "opus",
    "verifier": "opus",
    "executor": "sonnet",
    "github-issue-handler": "opus",
    "jira-code-plan": "opus",
    "slack-inquiry": "sonnet",
    "service-integrator": "sonnet",
}


def _parse_frontmatter_model(agent_file: Path) -> str | None:
    content = agent_file.read_text()
    if not content.startswith("---"):
        return None
    end = content.index("---", 3)
    frontmatter = content[3:end]
    match = re.search(r"^model:\s*(.+)$", frontmatter, re.MULTILINE)
    return match.group(1).strip() if match else None


class TestAgentFrontmatter:
    def test_each_agent_has_expected_model(self):
        for agent_name, expected_model in EXPECTED_MODELS.items():
            agent_file = AGENTS_DIR / f"{agent_name}.md"
            assert agent_file.exists(), f"{agent_name}.md not found"
            model = _parse_frontmatter_model(agent_file)
            assert model == expected_model, f"{agent_name} should use {expected_model}, got {model}"

    def test_all_agent_files_have_model(self):
        for agent_file in AGENTS_DIR.glob("*.md"):
            if agent_file.name == "MANIFEST.md":
                continue
            model = _parse_frontmatter_model(agent_file)
            assert model is not None, f"{agent_file.name} is missing 'model:' in frontmatter"
