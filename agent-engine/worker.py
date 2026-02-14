import asyncio
import os
import re
import time
from typing import Any

import redis.asyncio as redis
import structlog
from services import conversation_bridge, task_routing
from services.dashboard_client import post_assistant_message, update_dashboard_task
from services.knowledge import KnowledgeService, NoopKnowledgeService
from services.loop_tracking import extract_posted_comment_ids, track_posted_comments
from services.output_validation import clean_agent_output, detect_auth_failure
from services.redis_ops import persist_output, publish_task_event, update_task_status
from services.slack_notifier import (
    get_notification_channel,
    notify_task_completed,
    notify_task_failed,
)

logger = structlog.get_logger(__name__)

POSTING_TOOL_NAMES = {"send_slack_message", "add_issue_comment", "add_jira_comment"}

_PR_URL_PATTERN = re.compile(r"https://github\.com/[^\s\)\]]+/pull/\d+")


def _extract_pr_url(output: str) -> str:
    match = _PR_URL_PATTERN.search(output)
    return match.group(0) if match else ""


def _build_view_url(task: dict[str, Any], output: str = "") -> str:
    pr_url = _extract_pr_url(output) if output else ""
    if pr_url:
        return pr_url

    source = task.get("source", "")
    if source == "github":
        full_name = task.get("repository", {}).get("full_name", "")
        pr = task.get("pull_request", {})
        issue = task.get("issue", {})
        number = pr.get("number") or issue.get("number")
        if full_name and number:
            return f"https://github.com/{full_name}/issues/{number}"
    return ""


def _extract_mcp_posted_content(tool_events: list[dict] | None) -> str | None:
    if not tool_events:
        return None
    for event in tool_events:
        if event.get("type") != "tool_call":
            continue
        tool_name = event.get("name", "")
        if not any(posting in tool_name for posting in POSTING_TOOL_NAMES):
            continue
        tool_input = event.get("input", {})
        text = tool_input.get("text") or tool_input.get("body") or tool_input.get("commentBody")
        if text:
            return str(text)[:10000]
    return None


class TaskWorker:
    def __init__(
        self,
        settings: Any,
        knowledge_service: KnowledgeService | NoopKnowledgeService,
    ):
        self._settings = settings
        self._redis: redis.Redis | None = None
        self._running = False
        self._knowledge = knowledge_service

    async def start(self) -> None:
        self._redis = redis.from_url(self._settings.redis_url)
        self._running = True
        logger.info("task_worker_started", max_concurrent=self._settings.max_concurrent_tasks)

        semaphore = asyncio.Semaphore(self._settings.max_concurrent_tasks)

        while self._running:
            try:
                task_data = await self._redis.brpop("agent:tasks", timeout=1)
                if task_data:
                    async with semaphore:
                        asyncio.create_task(self._process_task(task_data[1]))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("worker_error", error=str(e))
                await asyncio.sleep(1)

    async def _process_task(self, task_data: bytes) -> None:
        import json

        try:
            task = json.loads(task_data)
            task_id = task.get("task_id", "unknown")
            session_id = task.get("session_id")
            conversation_id = task.get("conversation_id")
            webhook_conversation_id: str | None = None
            logger.info("task_started", task_id=task_id)

            source = task.get("source", "unknown")
            event_type_key = task.get("event_type", "unknown")
            target_agent = "brain"
            task["assigned_agent"] = target_agent

            for event_type, extra in [
                (
                    "task:created",
                    {
                        "input_message": task.get("prompt", ""),
                        "source": source,
                        "assigned_agent": target_agent,
                    },
                ),
                ("task:started", {"conversation_id": conversation_id}),
            ]:
                await publish_task_event(
                    self._redis,
                    task_id,
                    event_type,
                    {"task_id": task_id, "session_id": session_id, **extra},
                )

            dashboard_url = os.getenv("DASHBOARD_API_URL", "http://dashboard-api:5000")
            enriched_prompt = task.get("prompt", "")

            if source in ("github", "jira", "slack"):
                enriched_prompt = await self._build_webhook_context(
                    task, dashboard_url, task_id, session_id
                )
                webhook_conversation_id = task.get("_webhook_conversation_id")
                if not session_id:
                    session_id = webhook_conversation_id

                await publish_task_event(
                    self._redis,
                    task_id,
                    "task:context_built",
                    {
                        "task_id": task_id,
                        "enriched_prompt": enriched_prompt[:50000],
                        "flow_id": conversation_bridge.build_flow_id(task),
                        "conversation_id": webhook_conversation_id,
                        "source_metadata": {"source": source, "event_type": event_type_key},
                    },
                )

            await update_task_status(self._redis, task_id, "in_progress")
            await update_dashboard_task(dashboard_url, task_id, {"status": "running"})
            start_time = time.monotonic()

            task_with_enriched_prompt = {**task, "prompt": enriched_prompt}
            result = await self._execute_task(task_with_enriched_prompt)
            duration = time.monotonic() - start_time
            await update_task_status(self._redis, task_id, "completed", result)

            await self._publish_raw_output(task_id, result)

            raw_output = result.get("output", "")
            full_output = result.get("raw_output", raw_output)
            mcp_already_posted = task_routing.detect_mcp_posting(full_output)
            output = clean_agent_output(raw_output) if raw_output else ""

            if mcp_already_posted:
                mcp_content = _extract_mcp_posted_content(result.get("tool_events"))
                if mcp_content:
                    output = mcp_content

            result["output"] = output
            if output:
                await persist_output(self._redis, task_id, output)
                await publish_task_event(
                    self._redis,
                    task_id,
                    "task:output",
                    {"task_id": task_id, "content": output},
                )

            auth_error = detect_auth_failure(output) if output else None
            if auth_error:
                result["success"] = False
                result["error"] = f"Authentication failure detected: {auth_error}"
                logger.warning("auth_failure_detected", task_id=task_id, pattern=auth_error)

            status = "completed" if result.get("success", True) else "failed"
            await publish_task_event(
                self._redis,
                task_id,
                "task:completed",
                {
                    "task_id": task_id,
                    "session_id": session_id,
                    "conversation_id": conversation_id,
                    "status": status,
                    "result": output,
                    "duration_seconds": round(duration, 2),
                    "cost_usd": result.get("cost_usd"),
                    "input_tokens": result.get("input_tokens"),
                    "output_tokens": result.get("output_tokens"),
                },
            )

            await update_dashboard_task(
                dashboard_url,
                task_id,
                {
                    "status": status,
                    "output": output[:10000] if output else "",
                    "error": result.get("error"),
                    "cost_usd": result.get("cost_usd"),
                    "input_tokens": result.get("input_tokens"),
                    "output_tokens": result.get("output_tokens"),
                    "duration_seconds": round(duration, 2),
                },
            )

            target_conversation = conversation_id or webhook_conversation_id
            if target_conversation and result.get("output"):
                await post_assistant_message(
                    dashboard_url, target_conversation, result["output"], task_id
                )

            if source in ("github", "jira", "slack"):
                await self._handle_response_posting(
                    task,
                    result,
                    task_id,
                    source,
                    mcp_already_posted,
                    webhook_conversation_id,
                    dashboard_url,
                )

            slack_url = self._settings.slack_api_url
            slack_ch = await get_notification_channel(
                self._settings.oauth_service_url,
                self._settings.internal_service_key,
                self._settings.slack_notification_channel,
            )
            if status == "completed":
                view_url = _build_view_url(task, output)
                await notify_task_completed(
                    slack_url, slack_ch, source, task_id, output[:500] or "Done", view_url
                )
            elif status == "failed":
                await notify_task_failed(
                    slack_url, slack_ch, source, task_id, result.get("error", "")
                )
            logger.info("task_completed", task_id=task_id)
        except Exception as e:
            logger.exception("task_failed", error=str(e))
            if "task_id" in locals():
                await update_task_status(self._redis, task_id, "failed", {"error": str(e)})
                await update_dashboard_task(
                    dashboard_url, task_id, {"status": "failed", "error": str(e)}
                )
                await publish_task_event(
                    self._redis,
                    task_id,
                    "task:failed",
                    {"task_id": task_id, "error": str(e)},
                )
                await notify_task_failed(
                    self._settings.slack_api_url,
                    self._settings.slack_notification_channel,
                    locals().get("source", "unknown"),
                    task_id,
                    str(e),
                )

    async def _build_webhook_context(
        self, task: dict, dashboard_url: str, task_id: str, session_id: str | None
    ) -> str:
        flow_id = conversation_bridge.build_flow_id(task)
        logger.info("webhook_flow_started", task_id=task_id, flow_id=flow_id)

        webhook_conversation_id = await conversation_bridge.get_or_create_flow_conversation(
            dashboard_url, task
        )
        logger.info(
            "webhook_conversation_ready", task_id=task_id, conversation_id=webhook_conversation_id
        )

        await conversation_bridge.register_task(dashboard_url, task, webhook_conversation_id)
        logger.info("webhook_task_registered", task_id=task_id, session_id=session_id)

        await conversation_bridge.post_system_message(
            dashboard_url, webhook_conversation_id, task, task_id=task_id
        )

        conversation_context = await conversation_bridge.fetch_conversation_context(
            dashboard_url,
            webhook_conversation_id,
            limit=5,
            roles="user,assistant",
        )
        logger.info(
            "webhook_context_fetched", task_id=task_id, messages_count=len(conversation_context)
        )

        task["_webhook_conversation_id"] = webhook_conversation_id
        return await task_routing.build_task_context(task, conversation_context)

    async def _publish_raw_output(self, task_id: str, result: dict[str, Any]) -> None:
        raw_for_event = result.get("raw_output", result.get("output", ""))
        await publish_task_event(
            self._redis,
            task_id,
            "task:raw_output",
            {
                "task_id": task_id,
                "raw_output": raw_for_event[:204800],
            },
        )

    async def _handle_response_posting(
        self,
        task: dict,
        result: dict,
        task_id: str,
        source: str,
        mcp_already_posted: bool,
        webhook_conversation_id: str | None,
        dashboard_url: str,
    ) -> None:
        mcp_posted = mcp_already_posted
        fallback_posted = False

        if mcp_posted:
            logger.info("mcp_response_posted", task_id=task_id, source=source)
            comment_ids = extract_posted_comment_ids(result.get("tool_events"))
            await track_posted_comments(self._redis, comment_ids, task_id, "mcp")
        else:
            from services.response_poster import post_response_to_platform

            post_result = await post_response_to_platform(task, result)
            if isinstance(post_result, dict):
                fallback_posted = post_result.get("posted", False)
                comment_id = post_result.get("comment_id")
                if comment_id:
                    await track_posted_comments(self._redis, [str(comment_id)], task_id, "fallback")
            else:
                fallback_posted = bool(post_result)
            logger.info(
                "fallback_response_posted", task_id=task_id, source=source, posted=fallback_posted
            )

            if webhook_conversation_id:
                await conversation_bridge.post_fallback_notice(
                    dashboard_url,
                    webhook_conversation_id,
                    source,
                    fallback_posted,
                    task_id=task_id,
                )

        response_method = "mcp" if mcp_posted else ("fallback" if fallback_posted else "failed")
        await publish_task_event(
            self._redis,
            task_id,
            "task:response_posted",
            {
                "task_id": task_id,
                "method": response_method,
                "source": source,
                "mcp_detected": mcp_posted,
                "fallback_posted": fallback_posted,
            },
        )

    async def _execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        from pathlib import Path

        from cli.factory import run_cli

        prompt = task.get("prompt", "")
        repo_path = task.get("repo_path", "/app")
        task_id = task.get("task_id", "unknown")
        target_agent = task.get("assigned_agent")

        output_queue: asyncio.Queue[str | None] = asyncio.Queue()

        async def _stream_event(event_type: str, event_data: dict[str, Any]) -> None:
            await publish_task_event(
                self._redis,
                task_id,
                event_type,
                {
                    "task_id": task_id,
                    **event_data,
                },
            )

        try:
            result = await run_cli(
                prompt=prompt,
                working_dir=Path(repo_path),
                output_queue=output_queue,
                task_id=task_id,
                timeout_seconds=self._settings.task_timeout_seconds,
                agents=target_agent,
                event_callback=_stream_event,
            )

            return {
                "output": result.clean_output or result.output,
                "raw_output": result.output,
                "cost_usd": result.cost_usd,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "success": result.success,
                "error": result.error,
                "tool_events": result.tool_events,
                "thinking_blocks": result.thinking_blocks,
            }
        except TimeoutError:
            return {"error": "Task timed out", "return_code": -1}

    async def stop(self) -> None:
        self._running = False
        if self._redis:
            await self._redis.aclose()
        logger.info("task_worker_stopped")
