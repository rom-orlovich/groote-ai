import json
import os
import subprocess
import sys
import time
from pathlib import Path

import redis

PROJECT_ROOT = Path(__file__).parents[2]
START_SCRIPT = PROJECT_ROOT / "scripts" / "cli" / "start.sh"
STOP_SCRIPT = PROJECT_ROOT / "scripts" / "cli" / "stop.sh"
QUEUE_KEY = "queue:cli:scaling"
POLL_TIMEOUT = 5


def get_redis_url() -> str:
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("REDIS_URL=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("REDIS_URL", "redis://localhost:6379/0")


def handle_scaling_message(data: str) -> None:
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        print(f"[watcher] Invalid JSON: {data}", flush=True)
        return

    provider = payload.get("provider", "claude")
    action = payload.get("action", "scale")
    agent_count = payload.get("agent_count", 1)

    if action == "stop" or agent_count == 0:
        print(f"[watcher] Stopping {provider} CLI...", flush=True)
        cmd = ["bash", str(STOP_SCRIPT), provider]
    else:
        print(f"[watcher] Scaling {provider} to {agent_count} agent(s)...", flush=True)
        cmd = ["bash", str(START_SCRIPT), provider, str(agent_count)]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print(f"[watcher] Command complete: {result.stdout.strip()}", flush=True)
        else:
            print(f"[watcher] Command failed: {result.stderr.strip()}", file=sys.stderr, flush=True)
    except subprocess.TimeoutExpired:
        print("[watcher] Command timed out after 120s", file=sys.stderr, flush=True)
    except Exception as exc:
        print(f"[watcher] Command error: {exc}", file=sys.stderr, flush=True)


def main() -> None:
    redis_url = get_redis_url()
    print(f"[watcher] Connecting to Redis: {redis_url}", flush=True)
    print(f"[watcher] Listening on queue: {QUEUE_KEY}", flush=True)

    while True:
        try:
            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()
            print("[watcher] Connected. Waiting for scaling commands...", flush=True)

            while True:
                result = client.brpop(QUEUE_KEY, timeout=POLL_TIMEOUT)
                if result:
                    _, data = result
                    handle_scaling_message(data)

        except redis.ConnectionError:
            print(
                "[watcher] Redis connection lost. Reconnecting in 5s...",
                file=sys.stderr,
                flush=True,
            )
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n[watcher] Shutting down.", flush=True)
            break


if __name__ == "__main__":
    main()
