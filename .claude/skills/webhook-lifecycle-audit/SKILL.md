---
name: webhook-lifecycle-audit
description: Run the end-to-end webhook audit system that fires real webhooks through the full pipeline and verifies every component responds correctly. Uses the scripts/audit framework.
user_invocable: true
---

# Webhook Lifecycle Audit

Runs the `scripts/audit` framework — an end-to-end audit that fires real webhooks through the full Groote AI pipeline and grades every component on correctness and quality.

## Arguments

- `source` (optional): Category to test — `all`, `github`, `jira`, `slack`, `chain`, or `knowledge`. Can also be specific flow IDs like `f01`, `f03`. Defaults to `all`.
- `--dry-run` (optional): Only check service health without running flows.
- `--verbose` (optional): Enable debug logging.
- `--timeout-multiplier N` (optional): Multiply all timeouts by N for slow environments.
- `--quality-threshold N` (optional): Minimum quality score to pass (default: 70).

## Available Flows

| Flow ID | Alias | Name | Description |
|---------|-------|------|-------------|
| f01 | slack | Slack Knowledge Query | Slack question routed to slack-inquiry agent with knowledge tools |
| f02 | jira | Jira Code Plan | Jira issue triggers code planning with knowledge retrieval |
| f03 | github | GitHub Issue Handler | GitHub issue triggers investigation and comment response |
| f04 | github | GitHub PR Review | PR triggers code review with diff analysis |
| f05 | jira | Jira Status Transition | Jira status change triggers cross-platform sync |
| f06 | chain | Chained Flow | Multi-step cross-platform orchestration |
| f07 | knowledge | Knowledge Refresh | Re-indexing and knowledge layer verification |

## Execution Steps

### Step 1: Check Prerequisites

Verify services are running before launching the audit:

```bash
make health
```

All of these must be healthy: API Gateway (8000), Dashboard API (3005), Task Logger (8090).

If `--dry-run` was specified, stop here and report health status.

### Step 2: Determine Flow Selection

Map the user's `source` argument to audit flow flags:

| User says | Runs |
|-----------|------|
| (nothing) or `all` | `--flow all` (f01-f07) |
| `github` | `--flow github` (f03, f04) |
| `jira` | `--flow jira` (f02, f05) |
| `slack` | `--flow slack` (f01) |
| `chain` | `--flow chain` (f06) |
| `knowledge` | `--flow knowledge` (f07) |
| `f01 f03` | `--flow f01 f03` (specific flows) |

### Step 3: Run the Audit

Execute from the project root:

```bash
python -m scripts.audit --flow {resolved_flows} --verbose
```

Add flags based on user arguments:
- `--timeout-multiplier {N}` if the user requested slower timeouts
- `--quality-threshold {N}` if the user set a custom threshold
- `--cleanup` if the user wants artifacts removed after run
- `--slack-channel {channel}` if overriding the default

The audit framework handles everything automatically:
1. Prerequisite health checks
2. Redis event stream monitoring
3. Real webhook trigger for each flow
4. Pipeline tracking through all 10 components
5. Quality scoring across 8 dimensions
6. Evidence collection and report generation

### Step 4: Report Results

The framework prints a terminal report and saves detailed results to `audit-results/<timestamp>/`.

After the command completes, summarize:
- Overall pass/fail count
- Average quality score
- Any failed flows with their error details
- Path to the full evidence directory

## Failure Diagnostics

If the audit fails, check these based on what went wrong:

| Symptom | Action |
|---------|--------|
| Prerequisite check failed | `make up` then `make health` |
| Webhook not received | `docker logs groote-ai-api-gateway-1 --tail 50` |
| Task never picked up | `docker logs groote-ai-cli-1 --tail 50` |
| Conversation not created | `docker logs groote-ai-dashboard-api-1 --tail 50` |
| Task Logger missing events | `curl http://localhost:8090/metrics` for queue lag |
| Timeout on execution | Retry with `--timeout-multiplier 2.0` or `3.0` |
| Knowledge flows failing | Verify manga-creator is indexed in vector store + knowledge graph |
| Jira flows failing | Ensure `AUDIT` project exists in Jira |
| Slack flows failing | Set `AUDIT_SLACK_CHANNEL` env var to a valid channel |

For any failure, include the last 20 lines of the relevant container logs in the report.

## Environment Variables

These can be set in `.env` or exported before running:

| Variable | Default | Description |
|----------|---------|-------------|
| `AUDIT_SLACK_CHANNEL` | `C_audit_test` | Slack channel for audit messages |
| `AUDIT_GITHUB_OWNER` | `rom-orlovich` | GitHub repo owner |
| `AUDIT_GITHUB_REPO` | `manga-creator` | GitHub repo name |
| `AUDIT_JIRA_PROJECT` | `AUDIT` | Jira project key |
| `AUDIT_API_GATEWAY_URL` | `http://localhost:8000` | API Gateway URL |
| `AUDIT_DASHBOARD_API_URL` | `http://localhost:3005` | Dashboard API URL |
| `AUDIT_TASK_LOGGER_URL` | `http://localhost:8090` | Task Logger URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `AUDIT_TIMEOUT_MULTIPLIER` | `1.0` | Global timeout multiplier |
| `AUDIT_QUALITY_THRESHOLD` | `70` | Minimum quality score to pass |
| `AUDIT_OUTPUT_DIR` | `./audit-results` | Output directory |

## Quality Scoring

Each flow is graded across 8 weighted dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| Routing Accuracy | 20% | Correct agent selected |
| Tool Efficiency | 15% | Right tools called without redundancy |
| Knowledge Utilization | 10% | Knowledge layer used when applicable |
| Response Completeness | 15% | Output contains expected patterns |
| Response Relevance | 10% | Domain-specific terminology present |
| Delivery Success | 15% | Response posted to originating platform |
| Execution Metrics | 10% | Completed within time bounds |
| Error Freedom | 5% | No errors in event stream |

Overall score = weighted average. Default pass threshold: 70/100.
