# Audit Framework Development Rules

## Code Standards

- Maximum 300 lines per file
- No comments in code -- self-explanatory names only
- Strict Pydantic models: `ConfigDict(strict=True)` on every model
- Async/await for all I/O operations
- Use relative imports within the `scripts.audit` package
- Structured logging: `logger.info("event_name", extra={"key": value})`

## File Structure

```
scripts/audit/
  __main__.py          # Entry point
  __init__.py          # Package marker
  run.py               # CLI orchestrator (argparse + flow execution)
  config.py            # AuditConfig model + load_config()
  core/
    client.py          # AuditClient (httpx + redis async client)
    redis_monitor.py   # Redis stream event monitoring
    evidence.py        # Evidence file collection and saving
    evaluator.py       # 8-dimension quality scoring
    report.py          # Report models + terminal/JSON generation
    checkpoint.py      # Checkpoint timing verification
    component_monitor.py  # 10-component health verification
  flows/
    __init__.py        # FLOW_REGISTRY dict mapping flow IDs to classes
    base.py            # BaseFlow ABC with run() orchestration
    f01_slack_knowledge.py
    f02_jira_code_plan.py
    ...
  triggers/
    __init__.py
    base.py            # TriggerResult model
    slack.py           # Slack message triggers
    jira.py            # Jira issue/transition triggers
    github.py          # GitHub issue/PR triggers
```

## Adding a New Flow

1. Create `flows/fNN_name.py` with a class extending `BaseFlow`
2. Set class attributes `name` and `description`
3. Implement three required methods:
   - `trigger()` -> `TriggerResult`: Fire the real webhook trigger
   - `expected_agent()` -> `str`: Return the agent name that should handle this
   - `flow_criteria()` -> `FlowCriteria`: Define quality evaluation criteria
4. Register in `flows/__init__.py` by adding `"fNN": FNNNameFlow` to `FLOW_REGISTRY`
5. Optionally override `cleanup()` to remove audit artifacts
6. Optionally override `requires_knowledge()` to return `False` if no knowledge lookup expected

## Testing

Flows ARE the tests. Run individual flows to verify:

```bash
python -m scripts.audit --flow fNN --verbose
```

There are no separate unit tests for flows. The audit framework itself validates correctness through real end-to-end execution with rigid pass/fail criteria.

## Key Models

- `AuditConfig`: All configuration with env var loading
- `FlowResult`: Output of a single flow execution
- `FlowReport`: Report-ready version with quality data
- `AuditReport`: Full audit run with all flows
- `QualityReport`: 8-dimension quality evaluation
- `FlowCriteria`: Expected behavior definition for quality scoring
- `TriggerResult`: Output of a trigger (platform, artifact_id, flow_id)
