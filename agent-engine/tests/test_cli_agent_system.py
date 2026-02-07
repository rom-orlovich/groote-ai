"""Tests that the CLI agent system works for both Claude and Cursor providers.

Verifies:
- Command construction does NOT pass --model (handled by agent frontmatter)
- Agent .md files are correctly structured for both CLIs
- Dockerfile copies agents to user-level directories (~/.claude/agents, ~/.cursor/agents)
- Both providers can be instantiated and build valid commands
"""

import re
from pathlib import Path

from cli.providers.claude import ClaudeCLIRunner
from cli.providers.cursor import CursorCLIRunner

AGENTS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "agents"
DOCKERFILE_PATH = Path(__file__).resolve().parent.parent / "Dockerfile"

REQUIRED_FRONTMATTER_FIELDS = {"name", "description", "model"}


def _parse_frontmatter(agent_file: Path) -> dict[str, str]:
    content = agent_file.read_text()
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    frontmatter_text = content[3:end]
    result = {}
    for line in frontmatter_text.strip().splitlines():
        match = re.match(r"^(\w+):\s*(.+)$", line)
        if match:
            result[match.group(1)] = match.group(2).strip()
    return result


class TestClaudeCLIAgentSystem:

    def test_command_does_not_include_model_flag(self):
        runner = ClaudeCLIRunner()
        cmd = runner._build_command(
            prompt="test prompt",
            model=None,
            allowed_tools=None,
            agents=None,
            debug_mode=None,
        )
        assert "--model" not in cmd

    def test_command_uses_print_mode(self):
        runner = ClaudeCLIRunner()
        cmd = runner._build_command(
            prompt="test", model=None, allowed_tools=None,
            agents=None, debug_mode=None,
        )
        assert "-p" in cmd
        assert "--output-format" in cmd
        assert "stream-json" in cmd

    def test_command_skips_permissions(self):
        runner = ClaudeCLIRunner()
        cmd = runner._build_command(
            prompt="test", model=None, allowed_tools=None,
            agents=None, debug_mode=None,
        )
        assert "--dangerously-skip-permissions" in cmd

    def test_agents_flag_passthrough(self):
        runner = ClaudeCLIRunner()
        agents_json = '{"brain": {"model": "opus"}}'
        cmd = runner._build_command(
            prompt="test", model=None, allowed_tools=None,
            agents=agents_json, debug_mode=None,
        )
        assert "--agents" in cmd
        idx = cmd.index("--agents")
        assert cmd[idx + 1] == agents_json


class TestCursorCLIAgentSystem:

    def test_command_does_not_include_model_flag(self):
        runner = CursorCLIRunner()
        cmd = runner._build_command(
            prompt="test prompt", model=None, mode=None, force=True,
        )
        assert "-m" not in cmd

    def test_command_uses_print_mode(self):
        runner = CursorCLIRunner()
        cmd = runner._build_command(
            prompt="test", model=None, mode=None, force=True,
        )
        assert "-p" in cmd
        assert "--output-format" in cmd
        assert "stream-json" in cmd

    def test_command_uses_force_flag(self):
        runner = CursorCLIRunner()
        cmd = runner._build_command(
            prompt="test", model=None, mode=None, force=True,
        )
        assert "-f" in cmd


class TestAgentFilesStructure:

    def test_all_agents_have_required_fields(self):
        for agent_file in AGENTS_DIR.glob("*.md"):
            frontmatter = _parse_frontmatter(agent_file)
            for field in REQUIRED_FRONTMATTER_FIELDS:
                assert field in frontmatter, (
                    f"{agent_file.name} missing required field: {field}"
                )

    def test_model_values_are_valid(self):
        valid_models = {"opus", "sonnet", "haiku", "inherit"}
        for agent_file in AGENTS_DIR.glob("*.md"):
            frontmatter = _parse_frontmatter(agent_file)
            model = frontmatter.get("model")
            assert model in valid_models, (
                f"{agent_file.name} has invalid model: {model}"
            )


class TestDockerfileAgentCopy:

    def test_dockerfile_copies_agents_to_claude_home(self):
        content = DOCKERFILE_PATH.read_text()
        assert "/home/agent/.claude/agents" in content

    def test_dockerfile_copies_agents_to_cursor_home(self):
        content = DOCKERFILE_PATH.read_text()
        assert "/home/agent/.cursor/agents" in content
