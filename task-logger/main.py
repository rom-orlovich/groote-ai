import asyncio
import contextlib
import json
import logging

import redis.asyncio as redis
import uvicorn
from config import settings
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from worker import run as worker_run

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Task Logger Service", version="1.0.0")

worker_task = None


@app.on_event("startup")
async def startup():
    global worker_task
    worker_task = asyncio.create_task(worker_run())
    logger.info("task_logger_started port=%s", settings.port)


@app.on_event("shutdown")
async def shutdown():
    global worker_task
    if worker_task:
        worker_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker_task
    logger.info("task_logger_stopped")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "task-logger"}


def _resolve_task_dir(task_id: str):
    symlink_dir = settings.logs_dir / ".by-id" / task_id
    if symlink_dir.exists():
        return symlink_dir.resolve()
    direct_dir = settings.logs_dir / task_id
    if direct_dir.exists():
        return direct_dir
    return None


@app.get("/tasks/{task_id}/logs")
async def get_task_logs(task_id: str):
    task_dir = _resolve_task_dir(task_id)

    if not task_dir:
        raise HTTPException(status_code=404, detail="Task not found")

    logs = {}

    metadata_file = task_dir / "metadata.json"
    if metadata_file.exists():
        logs["metadata"] = json.loads(metadata_file.read_text())

    input_file = task_dir / "01-input.json"
    if input_file.exists():
        logs["input"] = json.loads(input_file.read_text())

    user_inputs_file = task_dir / "02-user-inputs.jsonl"
    if user_inputs_file.exists():
        logs["user_inputs"] = [
            json.loads(line) for line in user_inputs_file.read_text().splitlines()
        ]

    webhook_flow_file = task_dir / "03-webhook-flow.jsonl"
    if webhook_flow_file.exists():
        logs["webhook_flow"] = [
            json.loads(line) for line in webhook_flow_file.read_text().splitlines()
        ]

    agent_output_file = task_dir / "04-agent-output.jsonl"
    if agent_output_file.exists():
        logs["agent_output"] = [
            json.loads(line) for line in agent_output_file.read_text().splitlines()
        ]

    knowledge_file = task_dir / "05-knowledge-interactions.jsonl"
    if knowledge_file.exists():
        logs["knowledge_interactions"] = [
            json.loads(line) for line in knowledge_file.read_text().splitlines()
        ]

    final_result_file = task_dir / "06-final-result.json"
    if final_result_file.exists():
        logs["final_result"] = json.loads(final_result_file.read_text())

    response_posting_file = task_dir / "07-response-posting.jsonl"
    if response_posting_file.exists():
        logs["response_posting"] = [
            json.loads(line) for line in response_posting_file.read_text().splitlines()
        ]

    return JSONResponse(content=logs)


@app.get("/metrics")
async def get_metrics():
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)

    try:
        stream_info = await redis_client.xinfo_stream(settings.redis_stream)
        stream_length = stream_info.get("length", 0)

        groups_info = await redis_client.xinfo_groups(settings.redis_stream)
        lag = 0
        for group in groups_info:
            if group.get("name") == settings.redis_consumer_group:
                lag = group.get("lag", 0)
                break

        tasks_processed = len([
            d for d in settings.logs_dir.iterdir()
            if d.is_dir() and d.name != ".by-id"
        ])

        return {
            "queue_depth": stream_length,
            "queue_lag": lag,
            "tasks_processed": tasks_processed,
        }
    except Exception as e:
        logger.error("metrics_error error=%s", str(e))
        return {"error": str(e)}
    finally:
        await redis_client.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
