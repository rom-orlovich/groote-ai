import asyncio
import json
import os
from pathlib import Path

import structlog

from cli.base import CLIResult
from cli.event_collector import (
    determine_error_message,
    handle_assistant_message,
    handle_user_message,
)

logger = structlog.get_logger()


class ClaudeCLIRunner:
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
    ) -> CLIResult:
        cmd = self._build_command(prompt, model, allowed_tools, agents, debug_mode)

        logger.info(
            "starting_claude_cli",
            task_id=task_id,
            working_dir=str(working_dir),
            agent=agents,
            cmd_args=" ".join(cmd[:8]),
        )

        run_env = {
            **os.environ,
            "CLAUDE_TASK_ID": task_id,
            "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
        }

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(working_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=1024 * 1024,
            env=run_env,
        )

        await output_queue.put(f"[CLI] Claude process started (PID: {process.pid})\n")

        accumulated_output: list[str] = []
        clean_output: list[str] = []
        result_text: str = ""
        cost_usd = 0.0
        input_tokens = 0
        output_tokens = 0
        cli_error_message: str | None = None
        has_streaming_output = False
        stderr_lines: list[str] = []
        tool_events: list[dict] = []
        thinking_blocks: list[dict] = []
        last_tool_name: list[str] = [""]

        try:

            async def read_stdout() -> None:
                nonlocal cost_usd, input_tokens, output_tokens, cli_error_message
                nonlocal has_streaming_output, result_text

                if not process.stdout:
                    return

                async for line in process.stdout:
                    line_str = line.decode(errors="replace").rstrip("\n\r")
                    if not line_str:
                        continue

                    try:
                        data = json.loads(line_str)
                        await self._handle_json_event(
                            data,
                            accumulated_output,
                            clean_output,
                            output_queue,
                            has_streaming_output,
                            tool_events,
                            thinking_blocks,
                            last_tool_name,
                        )

                        msg_type = data.get("type")
                        if msg_type == "stream_event":
                            event = data.get("event", {})
                            if event.get("type") == "content_block_delta":
                                has_streaming_output = True

                        if msg_type == "result":
                            cost_usd = data.get("total_cost_usd", data.get("cost_usd", 0.0))
                            usage = data.get("usage", {})
                            input_tokens = usage.get("input_tokens", 0)
                            output_tokens = usage.get("output_tokens", 0)
                            if data.get("is_error"):
                                cli_error_message = data.get("result", "")
                            else:
                                result_text = data.get("result", "")

                    except json.JSONDecodeError:
                        accumulated_output.append(line_str + "\n")
                        await output_queue.put(line_str + "\n")

            async def read_stderr() -> None:
                if not process.stderr:
                    return

                async for line in process.stderr:
                    line_str = line.decode().strip()
                    if line_str:
                        stderr_lines.append(line_str)
                        log_line = f"[LOG] {line_str}"
                        accumulated_output.append(log_line + "\n")
                        await output_queue.put(log_line + "\n")

            await asyncio.wait_for(
                asyncio.gather(read_stdout(), read_stderr()), timeout=timeout_seconds
            )
            await process.wait()
            await output_queue.put(None)

            error_msg = determine_error_message(
                process.returncode or 0, stderr_lines, cli_error_message
            )

            if stderr_lines:
                logger.warning(
                    "claude_cli_stderr",
                    task_id=task_id,
                    stderr="\n".join(stderr_lines[:10]),
                )

            logger.info(
                "claude_cli_completed",
                task_id=task_id,
                success=process.returncode == 0,
                cost_usd=cost_usd,
                return_code=process.returncode,
            )

            final_clean = result_text if result_text else "".join(clean_output)

            return CLIResult(
                success=process.returncode == 0,
                output="".join(accumulated_output),
                clean_output=final_clean,
                cost_usd=cost_usd,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                error=error_msg,
                tool_events=tool_events or None,
                thinking_blocks=thinking_blocks or None,
            )

        except TimeoutError:
            if process:
                process.kill()
                await process.wait()
            await output_queue.put(None)

            logger.error("claude_cli_timeout", task_id=task_id, timeout=timeout_seconds)

            return CLIResult(
                success=False,
                output="".join(accumulated_output),
                clean_output=result_text if result_text else "".join(clean_output),
                cost_usd=cost_usd,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                error=f"Timeout after {timeout_seconds} seconds",
                tool_events=tool_events or None,
                thinking_blocks=thinking_blocks or None,
            )

        except Exception as e:
            if process:
                process.kill()
                await process.wait()
            await output_queue.put(None)

            logger.error("claude_cli_error", task_id=task_id, error=str(e), exc_info=True)

            return CLIResult(
                success=False,
                output="".join(accumulated_output),
                clean_output=result_text if result_text else "".join(clean_output),
                cost_usd=cost_usd,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                error=f"Unexpected error: {e!s}",
                tool_events=tool_events or None,
                thinking_blocks=thinking_blocks or None,
            )

    def _build_command(
        self,
        prompt: str,
        model: str | None,
        allowed_tools: str | None,
        agents: str | None,
        debug_mode: str | None,
    ) -> list[str]:
        cmd = [
            "claude",
            "-p",
            "--output-format",
            "stream-json",
            "--verbose",
            "--dangerously-skip-permissions",
            "--include-partial-messages",
        ]

        if agents:
            cmd.extend(["--agent", agents])

        if debug_mode is not None:
            if debug_mode:
                cmd.extend(["--debug", debug_mode])
            else:
                cmd.append("--debug")

        if model and not agents:
            cmd.extend(["--model", model])

        if allowed_tools:
            cmd.extend(["--allowedTools", allowed_tools])

        mcp_config = Path("/app/.claude/mcp.json")
        if mcp_config.exists():
            cmd.extend(["--mcp-config", str(mcp_config)])

        cmd.extend(["--", prompt])

        return cmd

    async def _handle_json_event(
        self,
        data: dict,
        accumulated_output: list[str],
        clean_output: list[str],
        output_queue: asyncio.Queue[str | None],
        has_streaming_output: bool,
        tool_events: list[dict],
        thinking_blocks: list[dict],
        last_tool_name: list[str],
    ) -> None:
        msg_type = data.get("type")

        if msg_type == "init":
            init_content = data.get("content", "")
            if init_content:
                accumulated_output.append(init_content)
                await output_queue.put(init_content)

        elif msg_type == "assistant":
            await handle_assistant_message(
                data,
                accumulated_output,
                clean_output,
                output_queue,
                has_streaming_output,
                tool_events,
                thinking_blocks,
                last_tool_name,
            )

        elif msg_type == "user":
            await handle_user_message(
                data, accumulated_output, output_queue, tool_events, last_tool_name
            )

        elif msg_type == "stream_event":
            event = data.get("event", {})
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    if text:
                        accumulated_output.append(text)
                        clean_output.append(text)

        elif msg_type == "result":
            if (rt := data.get("result", "")) and not data.get("is_error"):
                accumulated_output.append(rt)