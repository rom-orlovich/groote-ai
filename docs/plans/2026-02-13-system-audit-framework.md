# System Audit Framework

## Status: In Progress

## Context

There is no automated way to verify that end-to-end webhook flows work correctly across all services. Manual testing is error-prone, not repeatable, and does not catch regressions in the pipeline between webhook reception and platform response delivery.

## Decision

Build a real trigger-based audit framework at `scripts/audit/` that fires actual webhooks through the full pipeline and verifies every component responds correctly with rigid pass/fail criteria.

## Rationale: Real Triggers vs Simulated Webhooks

The framework uses real platform triggers (actual Slack messages, actual Jira issues, actual GitHub PRs) rather than synthetic webhook payloads because:

- **Signature validation**: Real webhooks carry valid HMAC signatures from the platforms. Synthetic payloads would skip this critical security check.
- **Platform state**: Real triggers create actual artifacts (issues, messages, PRs) that the agent must interact with via MCP tools. This validates the full round-trip.
- **Redis queuing**: Real webhooks flow through the API Gateway's deduplication, validation, and queuing logic. Synthetic payloads would bypass these.
- **Conversation threading**: Real triggers create deterministic flow IDs that the conversation bridge uses to thread related events.

## Architecture

### Pipeline Components (10 verified per flow)

1. Webhook Reception (API Gateway receives the webhook)
2. Signature Validation (HMAC/token verification passes)
3. Task Queuing (Redis queue entry created with task_id)
4. Conversation Bridge (Dashboard conversation created/reused via flow_id)
5. Task Routing (Correct agent selected based on event type)
6. Context Building (Conversation history loaded for agent context)
7. Agent Execution (CLI provider runs to completion)
8. Knowledge Query (Knowledge layer tools called when applicable)
9. Response Posting (MCP tool posts response to originating platform)
10. Platform Delivery (Response verified via platform API)

### Quality Evaluation (8 dimensions)

Each dimension scored 0-100 with weighted contribution:

| Dimension | Weight | Source |
|-----------|--------|--------|
| Routing Accuracy | 20% | task:routed event agent matches expected |
| Tool Efficiency | 15% | Required tools called, no excessive redundancy |
| Knowledge Utilization | 10% | Knowledge tools used when required |
| Response Completeness | 15% | Output patterns and length requirements met |
| Response Relevance | 10% | Domain terminology present in output |
| Delivery Success | 15% | Response posted via MCP to originating platform |
| Execution Metrics | 10% | Duration within acceptable bounds |
| Error Freedom | 5% | No error events in stream |

### Flow Registry

Seven initial flows covering all webhook sources:

- **f01**: Slack knowledge query (slack-inquiry agent)
- **f02**: Jira code plan (jira-code-plan agent)
- **f03**: GitHub issue handler (github-issue-handler agent)
- **f04**: GitHub PR review (github-pr-review agent)
- **f05**: Jira status transition (service-integrator agent)
- **f06**: Chained cross-platform flow (multi-agent)
- **f07**: Knowledge refresh (indexer)

## Alternatives Considered

| Approach | Why Rejected |
|----------|-------------|
| Unit tests per service | Too narrow -- cannot verify cross-service integration |
| Manual testing runbook | Not repeatable, prone to human error, no quality scoring |
| Synthetic webhook payloads | Skips signature validation, bypasses API Gateway logic |
| Integration test with mocked Redis | Misses real queuing behavior, deduplication, stream events |

## File Structure

```
scripts/audit/
  __main__.py           # CLI entry point
  run.py                # Orchestrator (argparse, flow execution, reporting)
  config.py             # AuditConfig with env var loading
  core/
    client.py           # Async HTTP + Redis client
    redis_monitor.py    # Redis stream event monitoring
    evidence.py         # Evidence file collection
    evaluator.py        # 8-dimension quality scoring
    report.py           # Terminal + JSON report generation
    checkpoint.py       # Checkpoint timing verification
    component_monitor.py # 10-component health checks
  flows/
    base.py             # BaseFlow ABC
    f01_slack_knowledge.py
    f02_jira_code_plan.py
    ...
  triggers/
    base.py             # TriggerResult model
    slack.py / jira.py / github.py
```

## Usage

```bash
python -m scripts.audit --flow all
python -m scripts.audit --flow slack jira --verbose
python -m scripts.audit --flow f01 --timeout-multiplier 2.0 --cleanup
```

## Verification

The framework is self-verifying: each flow defines its own pass criteria, and the report generator produces both machine-readable JSON and human-readable terminal output with evidence directories for forensic analysis.
