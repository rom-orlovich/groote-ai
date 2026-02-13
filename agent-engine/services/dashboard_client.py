import httpx
import structlog

logger = structlog.get_logger(__name__)


async def post_assistant_message(
    dashboard_url: str, conversation_id: str, content: str, task_id: str
) -> None:
    url = f"{dashboard_url}/api/conversations/{conversation_id}/messages"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                url, json={"role": "assistant", "content": content, "task_id": task_id}
            )
        logger.info(
            "assistant_message_posted",
            conversation_id=conversation_id,
            task_id=task_id,
        )
    except Exception as e:
        logger.error(
            "failed_to_post_assistant_message",
            conversation_id=conversation_id,
            error=str(e),
        )


async def update_dashboard_task(
    dashboard_url: str, task_id: str, update: dict[str, str | int | float | bool | None]
) -> None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.patch(
                f"{dashboard_url}/api/tasks/{task_id}",
                json={k: v for k, v in update.items() if v is not None},
            )
    except Exception as e:
        logger.warning(
            "dashboard_task_update_failed", task_id=task_id, error=str(e)
        )
