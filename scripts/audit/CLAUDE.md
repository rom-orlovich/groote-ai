# Audit Framework

End-to-end system audit framework that fires real webhooks through the full groote-ai pipeline and verifies every component responds correctly. Not a unit test suite -- exercises real platform interactions, Redis queuing, agent execution, and MCP tool responses.

## Entry Points

- `python -m scripts.audit --flow all` - Run all 8 flows
- `python -m scripts.audit --flow f01 f02` - Run specific flows
- `python -m scripts.audit --flow slack jira github` - Run by category

## Architecture

```
Trigger (Slack/Jira/GitHub) -> API Gateway webhook -> Redis queue
-> Agent Engine pickup -> CLI execution -> MCP tool calls
-> Response posted -> Quality evaluation -> Report generation
```

## Key Components

- **Flows** (8 registered): f01-f09 (no f03), each extends `BaseFlow`
- **Triggers** (3 types): `SlackTrigger`, `JiraTrigger`, `GitHubTrigger`
- **Quality Evaluator**: 10 scoring dimensions, weighted scoring
- **Component Monitor**: 10 pipeline components verified per flow
- **Evidence Collector**: Saves events, components, quality to JSON
- **Redis Monitor**: Real-time Redis stream event listener
- **Report Generator**: Terminal (ANSI) and JSON output

## Folder Structure

```
scripts/audit/
├── __main__.py           # Entry point
├── __init__.py
├── run.py                # CLI orchestrator (argparse + flow execution)
├── config.py             # AuditConfig model + load_config()
├── core/
│   ├── client.py         # AuditClient (httpx + redis async)
│   ├── redis_monitor.py  # Redis stream event monitoring
│   ├── evidence.py       # Evidence file collection
│   ├── evaluator.py      # Quality evaluation orchestrator
│   ├── scoring.py        # 10 scoring dimension functions
│   ├── models.py         # QualityReport, FlowCriteria, QualityDimension
│   ├── report.py         # AuditReport, FlowReport, ReportGenerator
│   ├── checkpoint.py     # CheckpointRunner with critical/non-critical
│   └── component_monitor.py  # 10-component health verification
├── flows/
│   ├── __init__.py       # FLOW_REGISTRY mapping
│   ├── base.py           # BaseFlow ABC with run() orchestration
│   ├── f01_slack_knowledge.py
│   ├── f02_jira_code_plan.py
│   ├── f04_github_pr_review.py
│   ├── f05_jira_comment.py
│   ├── f06_full_chain.py
│   ├── f07_knowledge_health.py
│   ├── f08_slack_multi_repo.py
│   └── f09_plan_approval_flow.py
├── triggers/
│   ├── __init__.py
│   ├── base.py           # TriggerResult model
│   ├── slack.py          # Slack message triggers
│   ├── jira.py           # Jira issue/comment triggers
│   └── github.py         # GitHub issue/PR triggers
└── docs/
    ├── ARCHITECTURE.md
    ├── features.md
    └── flows.md
```

## Adding a New Flow

1. Create `flows/fNN_name.py` extending `BaseFlow`
2. Set `name` and `description` class attributes
3. Implement `trigger()` -> `TriggerResult`
4. Implement `expected_agent()` -> `str`
5. Implement `flow_criteria()` -> `FlowCriteria`
6. Register in `flows/__init__.py` FLOW_REGISTRY
7. Optionally override `cleanup()` and `requires_knowledge()`

## Testing

Flows ARE the tests. Run individual flows to verify:

```bash
python -m scripts.audit --flow fNN --verbose
```

## Quality Dimensions (10)

| Dimension | Weight | Critical |
|-----------|--------|----------|
| Routing Accuracy | 15 | Yes |
| Content Quality | 15 | Yes |
| Tool Efficiency | 10 | No |
| Knowledge Utilization | 10 | No |
| Knowledge First | 10 | No |
| Response Completeness | 10 | No |
| Response Relevance | 10 | No |
| Delivery Success | 10 | No |
| Execution Metrics | 5 | No |
| Error Freedom | 5 | No |

## Environment Variables

```bash
AUDIT_SLACK_CHANNEL=C0A9D3BFK2P
AUDIT_GITHUB_OWNER=rom-orlovich
AUDIT_GITHUB_REPO=manga-creator
AUDIT_JIRA_PROJECT=KAN
AUDIT_API_GATEWAY_URL=http://localhost:8000
AUDIT_DASHBOARD_API_URL=http://localhost:3005
AUDIT_TASK_LOGGER_URL=http://localhost:8090
AUDIT_LLAMAINDEX_URL=http://localhost:8002
AUDIT_GKG_URL=http://localhost:8003
REDIS_URL=redis://localhost:6379/0
AUDIT_TIMEOUT_MULTIPLIER=1.0
AUDIT_QUALITY_THRESHOLD=70
SLACK_SIGNING_SECRET=
```

## Development Rules

- Maximum 300 lines per file
- No comments in code -- self-explanatory names only
- Strict Pydantic models: `ConfigDict(strict=True)`
- Async/await for all I/O
- Use relative imports within the package
- Structured logging: `logger.info("event_name", extra={"key": value})`
