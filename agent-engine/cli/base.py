import asyncio
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

EventCallback = Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]]


@dataclass
class CLIResult:
    success: bool
    output: str
    clean_output: str
    cost_usd: float
    input_tokens: int
    output_tokens: int
    error: str | None = None
    tool_events: list[dict] | None = None
    thinking_blocks: list[dict] | None = None


@runtime_checkable
class CLIRunner(Protocol):
    async def run(
        self,
        prompt: str,
        working_dir: Path,
        output_queue: asyncio.Queue[str | None],
        task_id: str = "",
        timeout_seconds: int = 3600,
        model: str | None = None,
        allowed_tools: str | None = None,
        agents: str | None = None,
        debug_mode: str | None = None,
        event_callback: EventCallback | None = None,
    ) -> CLIResult: ...
