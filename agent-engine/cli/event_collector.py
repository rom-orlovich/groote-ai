import asyncio

from cli.sanitization import contains_sensitive_data, sanitize_sensitive_content

EventCallbackType = object


async def handle_assistant_message(
    data: dict,
    accumulated_output: list[str],
    clean_output: list[str],
    output_queue: asyncio.Queue[str | None],
    has_streaming_output: bool,
    tool_events: list[dict],
    thinking_blocks: list[dict],
    last_tool_name: list[str],
    event_callback: object | None = None,
) -> None:
    message = data.get("message", {})
    content_blocks = message.get("content", [])

    for block in content_blocks:
        if not isinstance(block, dict):
            continue

        block_type = block.get("type")
        if block_type == "text":
            text_content = block.get("text", "")
            if text_content:
                event = {"type": "thinking", "content": text_content}
                thinking_blocks.append(event)
                if event_callback:
                    await event_callback("task:thinking", event)
                if not has_streaming_output:
                    clean_output.append(text_content)

        elif block_type == "tool_use":
            tool_name = block.get("name", "unknown")
            tool_input = block.get("input", {})
            tool_use_id = block.get("id", "")
            event = {
                "type": "tool_call",
                "name": tool_name,
                "input": tool_input,
                "_tool_use_id": tool_use_id,
            }
            tool_events.append(event)
            if event_callback:
                await event_callback("task:tool_call", event)
            last_tool_name[0] = tool_name
            tool_log = f"\n[TOOL] Using {tool_name}\n"
            if isinstance(tool_input, dict):
                if "command" in tool_input:
                    tool_log += f"  Command: {tool_input['command']}\n"
                elif "description" in tool_input:
                    tool_log += f"  {tool_input['description']}\n"
            accumulated_output.append(tool_log)
            await output_queue.put(tool_log)


async def handle_user_message(
    data: dict,
    accumulated_output: list[str],
    output_queue: asyncio.Queue[str | None],
    tool_events: list[dict],
    last_tool_name: list[str],
    event_callback: object | None = None,
) -> None:
    message = data.get("message", {})
    content = message.get("content", []) if isinstance(message, dict) else []

    pending_calls = [e for e in tool_events if e.get("type") == "tool_call"]
    matched_results = {e.get("name") for e in tool_events if e.get("type") == "tool_result"}
    unmatched_calls = [c for c in pending_calls if c.get("_matched") is not True]

    result_index = 0
    for block in content if isinstance(content, list) else []:
        if isinstance(block, dict) and block.get("type") == "tool_result":
            tool_content = block.get("content", "")
            is_error = block.get("is_error", False)
            tool_use_id = block.get("tool_use_id", "")
            resolved_name = last_tool_name[0]
            if tool_use_id:
                for call in reversed(tool_events):
                    if call.get("type") == "tool_call" and call.get("_tool_use_id") == tool_use_id:
                        resolved_name = call.get("name", resolved_name)
                        break
            elif result_index < len(unmatched_calls):
                resolved_name = unmatched_calls[result_index].get("name", resolved_name)
                unmatched_calls[result_index]["_matched"] = True
                result_index += 1
            if tool_content:
                event = {
                    "type": "tool_result",
                    "name": resolved_name,
                    "content": str(tool_content)[:5000],
                    "is_error": is_error,
                }
                tool_events.append(event)
                if event_callback:
                    await event_callback("task:tool_result", event)
                if contains_sensitive_data(tool_content):
                    tool_content = sanitize_sensitive_content(tool_content)
                prefix = "[TOOL ERROR] " if is_error else "[TOOL RESULT]\n"
                result_log = f"{prefix}{tool_content}\n"
                accumulated_output.append(result_log)
                await output_queue.put(result_log)


def determine_error_message(
    returncode: int,
    stderr_lines: list[str],
    cli_error_message: str | None,
) -> str | None:
    if returncode == 0:
        return None

    if cli_error_message:
        return cli_error_message

    if stderr_lines:
        cleaned_lines = [
            line for line in stderr_lines if not line.startswith("[LOG]") and line.strip()
        ]
        if cleaned_lines:
            return "\n".join(cleaned_lines) + f"\n\n(Exit code: {returncode})"
        return "\n".join(stderr_lines) + f"\n\n(Exit code: {returncode})"

    return f"Exit code: {returncode}"
