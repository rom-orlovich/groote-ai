import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path


def build_task_dir_name(task_id: str, source: str = "") -> str:
    ts = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S")
    short_id = task_id[:8]
    source_tag = f"_{source}" if source else ""
    return f"{ts}{source_tag}_{short_id}"


class TaskLogger:
    def __init__(self, task_id: str, logs_dir: Path, source: str = ""):
        self.task_id = task_id
        self._logs_dir = logs_dir
        dir_name = build_task_dir_name(task_id, source)
        self.log_dir = logs_dir / dir_name
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._create_id_symlink(logs_dir, task_id, dir_name)

    def _create_id_symlink(self, logs_dir: Path, task_id: str, dir_name: str) -> None:
        link_path = logs_dir / f".by-id" / task_id
        link_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if link_path.is_symlink() or link_path.exists():
                link_path.unlink()
            link_path.symlink_to(self.log_dir)
        except OSError:
            pass

    def write_metadata(self, data: dict):
        metadata_file = self.log_dir / "metadata.json"
        self._atomic_write_json(metadata_file, data)

    def write_input(self, data: dict):
        input_file = self.log_dir / "01-input.json"
        self._atomic_write_json(input_file, data)

    def append_user_input(self, user_input: dict):
        user_input_file = self.log_dir / "02-user-inputs.jsonl"
        self._atomic_append_jsonl(user_input_file, user_input)

    def append_webhook_event(self, event: dict):
        webhook_file = self.log_dir / "03-webhook-flow.jsonl"
        self._atomic_append_jsonl(webhook_file, event)

    def append_agent_output(self, output: dict):
        output_file = self.log_dir / "04-agent-output.jsonl"
        self._atomic_append_jsonl(output_file, output)

    def append_knowledge_interaction(self, interaction: dict):
        knowledge_file = self.log_dir / "05-knowledge-interactions.jsonl"
        self._atomic_append_jsonl(knowledge_file, interaction)

    def enrich_input(self, data: dict):
        input_file = self.log_dir / "01-input.json"
        existing = {}
        if input_file.exists():
            existing = json.loads(input_file.read_text())
        existing.update(data)
        self._atomic_write_json(input_file, existing)

    def enrich_metadata(self, data: dict):
        metadata_file = self.log_dir / "metadata.json"
        existing = {}
        if metadata_file.exists():
            existing = json.loads(metadata_file.read_text())
        existing.update(data)
        self._atomic_write_json(metadata_file, existing)

    def append_response_posting(self, event: dict):
        posting_file = self.log_dir / "07-response-posting.jsonl"
        self._atomic_append_jsonl(posting_file, event)

    def write_final_result(self, data: dict):
        result_file = self.log_dir / "06-final-result.json"
        self._atomic_write_json(result_file, data)

    def _atomic_write_json(self, file_path: Path, data: dict):
        temp_fd, temp_path = tempfile.mkstemp(dir=self.log_dir, suffix=".tmp")
        try:
            with os.fdopen(temp_fd, "w") as f:
                json.dump(data, f, indent=2)
            os.rename(temp_path, file_path)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def _atomic_append_jsonl(self, file_path: Path, data: dict):
        with open(file_path, "a") as f:
            f.write(json.dumps(data) + "\n")
