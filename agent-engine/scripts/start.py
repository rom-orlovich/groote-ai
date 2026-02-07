#!/usr/bin/env python3
"""Startup script: setup config, test CLI, then run main app."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_CLAUDE_DIR = Path("/app/.claude")
CLAUDE_HOME = Path.home() / ".claude"
CURSOR_HOME = Path.home() / ".cursor"

CONFIG_ITEMS = ["agents", "skills", "CLAUDE.md", "mcp.json"]


def setup_cli_config():
    if not APP_CLAUDE_DIR.exists():
        print("No .claude config found in /app/.claude/")
        return

    for target_home in [CLAUDE_HOME, CURSOR_HOME]:
        target_home.mkdir(parents=True, exist_ok=True)

        for item in CONFIG_ITEMS:
            src = APP_CLAUDE_DIR / item
            dst = target_home / item
            if not src.exists():
                continue

            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

    agent_count = len(list((APP_CLAUDE_DIR / "agents").glob("*.md")))
    skill_count = len(list((APP_CLAUDE_DIR / "skills").iterdir())) - 1
    print(
        f"Synced config to ~/.claude/ and ~/.cursor/: "
        f"{agent_count} agents, {skill_count} skills, CLAUDE.md, mcp.json"
    )


def install_cursor_cli():
    cursor_path = os.path.expanduser("~/.local/bin/agent")
    if os.path.exists(cursor_path):
        return True

    print("Installing Cursor CLI...")
    result = subprocess.run(
        ["bash", "-c", "curl -fsSL https://cursor.com/install | bash"],
        capture_output=True,
    )
    if result.returncode == 0:
        print("Cursor CLI installed")
        return True
    print(f"Cursor CLI install failed: {result.stderr.decode()}")
    return False


def run_cli_test():
    print("Running unified CLI check...")
    result = subprocess.run([sys.executable, "scripts/test_cli.py"], cwd="/app")
    return result.returncode == 0


def main():
    provider = os.environ.get("CLI_PROVIDER", "claude")
    print(f"Starting agent-engine (provider: {provider})...")

    setup_cli_config()

    if provider == "cursor" and not install_cursor_cli():
        sys.exit(1)

    if not run_cli_test():
        print("")
        print("=" * 50)
        print("  CLI CHECK WARNING: Issues detected!")
        print(f"  Provider: {provider}")
        print("  Tasks may fail until resolved.")
        print("=" * 50)
        print("")

    print("Starting main application...")

    subprocess.Popen([sys.executable, "scripts/heartbeat.py"])

    os.execv(sys.executable, [sys.executable, "main.py"])


if __name__ == "__main__":
    main()
