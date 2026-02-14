# Groote AI End-to-End System Audit

Real trigger-based audit framework that fires actual webhooks through the full pipeline and verifies every component responds correctly. This is NOT a unit test suite -- it exercises real platform interactions, real Redis queuing, real agent execution, and real MCP tool responses.

## Prerequisites

Before running the audit:

1. **All services running**: `make up` from the project root
2. **manga-creator repo indexed**: The GitHub repo `rom-orlovich/manga-creator` must be indexed in the knowledge layer (vector store + knowledge graph)
3. **AUDIT Jira project**: A Jira project with key `AUDIT` must exist with at least one issue
4. **Slack channel configured**: Set `AUDIT_SLACK_CHANNEL` to a channel where the bot can post
5. **Webhook URLs configured**: `PUBLIC_URL` must be set and webhook endpoints registered with GitHub, Jira, and Slack
6. **Service health**: Verify with `make health` that API Gateway, Dashboard API, and Task Logger are healthy

## Quick Start

```bash
# Run all flows
python -m scripts.audit --flow all

# Run specific flows by ID
python -m scripts.audit --flow f01 f02 f03

# Run by category alias
python -m scripts.audit --flow slack jira github

# Run chain flow only
python -m scripts.audit --flow chain

# Increase timeouts for slow environments
python -m scripts.audit --timeout-multiplier 2.0

# Custom output directory
python -m scripts.audit --output-dir ./my-audit

# Clean up audit artifacts after run
python -m scripts.audit --cleanup

# Verbose logging (DEBUG level)
python -m scripts.audit --verbose

# Set quality pass threshold
python -m scripts.audit --quality-threshold 80

# Override Slack channel
python -m scripts.audit --slack-channel C12345678
```

## Flow Descriptions

| Flow ID | Name | Category | Description |
|---------|------|----------|-------------|
| f01 | Slack Knowledge Query | Slack | User asks about a repo in Slack. Verifies routing to slack-inquiry agent, knowledge tool usage, and Slack response delivery. |
| f02 | Jira Code Plan | Jira | New Jira issue triggers code planning. Verifies routing to jira-code-plan agent, knowledge retrieval, plan generation, and Jira comment delivery. |
| f04 | GitHub PR Review | GitHub | PR comment triggers code review. Verifies routing to github-pr-review agent, diff analysis, knowledge context, and PR review comment delivery. |
| f05 | Jira Comment | Jira | Jira comment triggers agent response. Verifies routing to jira-code-plan agent and comment delivery. |
| f06 | Full Chain | Chain | Multi-step flow: Jira issue triggers cross-platform orchestration. Verifies conversation threading and full pipeline. |
| f07 | Knowledge Health | Knowledge | Verifies knowledge layer services are healthy and responding to queries. |
| f08 | Slack Multi-Repo | Slack | Multi-repo question in Slack. Verifies knowledge search across repositories. |
| f09 | Plan Approval | Jira | Plan approval workflow via Jira. Verifies plan generation and approval flow. |

## Pass Criteria

Each flow must satisfy ALL of the following to pass:

- **Component Health**: All 10 pipeline components report healthy during execution
- **Checkpoint Completion**: Every checkpoint in the flow timeline completes within its timeout
- **Quality Score**: Weighted quality score meets threshold (default: 70/100)
- **Error Freedom**: No unrecoverable errors in the event stream

### Per-Flow Criteria

| Flow | Expected Agent | Key Required Tools | Response Tool |
|------|---------------|-------------------|---------------|
| f01 | slack-inquiry | knowledge_query | send_slack_message |
| f02 | jira-code-plan | knowledge_query | add_jira_comment |
| f04 | github-pr-review | knowledge_query | add_issue_comment |
| f05 | jira-code-plan | knowledge_query | add_jira_comment |
| f06 | jira-code-plan | knowledge_query | add_jira_comment |
| f07 | slack-inquiry | knowledge_query | send_slack_message |
| f08 | slack-inquiry | knowledge_query | send_slack_message |
| f09 | jira-code-plan | knowledge_query | add_jira_comment |

## Quality Scoring

Quality is evaluated across 10 dimensions, each scored 0-100 with weighted contribution to the overall score:

| Dimension | Weight | Critical | What It Measures |
|-----------|--------|----------|------------------|
| Routing Accuracy | 15 | Yes | Correct agent selected for the task |
| Content Quality | 15 | Yes | Output references target repo, no negative patterns, meets min length |
| Tool Efficiency | 10 | No | Required tools called without excessive redundancy |
| Knowledge Utilization | 10 | No | Knowledge layer tools used when applicable |
| Knowledge First | 10 | No | Knowledge tools called before domain action tools |
| Response Completeness | 10 | No | Output contains expected patterns and meets length requirements |
| Response Relevance | 10 | No | Output contains domain-specific terminology |
| Delivery Success | 10 | No | Response posted back to originating platform via MCP |
| Execution Metrics | 5 | No | Task completed within acceptable time bounds |
| Error Freedom | 5 | No | No errors in the event stream |

**Overall score** = weighted average of all dimensions. Default pass threshold is 70.

**Critical dimensions** (Routing Accuracy, Content Quality) force a fail if they score below 50, regardless of overall score.

## Component Monitoring

Each flow verifies that these 10 pipeline components participated correctly:

| Component | Verified By |
|-----------|-------------|
| Webhook Reception | `webhook:received` event in Redis stream |
| Signature Validation | `webhook:validated` event with valid signature |
| Task Queuing | `webhook:task_created` event with task_id |
| Conversation Bridge | Conversation created/found via Dashboard API |
| Task Routing | `task:routed` event with correct agent |
| Context Building | `task:context_built` event with conversation context |
| Agent Execution | `task:executing` through `task:completed` events |
| Knowledge Query | Tool call events for knowledge tools |
| Response Posting | `task:response_posted` event with MCP method |
| Platform Delivery | Verified via platform API (comment exists, message sent) |

## Output Directory Structure

Each audit run creates a timestamped directory:

```
audit-results/
  2026-02-13T14-30-00/
    report.json            # Machine-readable full report
    report.txt             # Terminal-formatted report (with ANSI codes)
    f01/
      events.json          # All Redis stream events for this flow
      components.json      # Component health status
      quality.json         # Quality evaluation breakdown
    f02/
      events.json
      components.json
      quality.json
    ...
```

## Troubleshooting

### Services not running

```
Prerequisite check failed (3 issues). Fix and retry.
```

Run `make up` and wait for all services to be healthy (`make health`).

### manga-creator not indexed

Flows that require knowledge (f01, f02, f04, f06) will fail with low Knowledge Utilization scores. Run the indexer:

```bash
docker compose exec indexer-worker python -m indexer_worker.worker --source github --repo rom-orlovich/manga-creator
```

### AUDIT Jira project missing

Jira flows (f02, f05, f06) will fail at the trigger step. Create a project with key `AUDIT` in your Jira instance.

### Webhook URLs not configured

Flows fail at the "Webhook Reception" component. Ensure `PUBLIC_URL` is set and webhook endpoints are registered:

- GitHub: `{PUBLIC_URL}/webhooks/github`
- Jira: `{PUBLIC_URL}/webhooks/jira`
- Slack: `{PUBLIC_URL}/webhooks/slack`

### Slack channel not set

Flow f01 will fail. Set the `AUDIT_SLACK_CHANNEL` environment variable or pass `--slack-channel`.

### Timeouts

If flows fail with `TimeoutError`, the environment may be slow. Increase timeouts:

```bash
python -m scripts.audit --timeout-multiplier 3.0
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams and data flows
- [Features](docs/features.md) - Feature list and capabilities
- [Flows](docs/flows.md) - Process flow documentation

## Adding New Flows

1. Create `scripts/audit/flows/fNN_name.py` with a class extending `BaseFlow`
2. Implement `trigger()`, `expected_agent()`, and `flow_criteria()`
3. Register in `scripts/audit/flows/__init__.py` by adding to `FLOW_REGISTRY`
4. Add a trigger class in `scripts/audit/triggers/` if needed

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUDIT_SLACK_CHANNEL` | `C_audit_test` | Slack channel for audit messages |
| `AUDIT_GITHUB_OWNER` | `rom-orlovich` | GitHub repo owner |
| `AUDIT_GITHUB_REPO` | `manga-creator` | GitHub repo name |
| `AUDIT_JIRA_PROJECT` | `AUDIT` | Jira project key |
| `AUDIT_API_GATEWAY_URL` | `http://localhost:8000` | API Gateway URL |
| `AUDIT_DASHBOARD_API_URL` | `http://localhost:5000` | Dashboard API URL |
| `AUDIT_TASK_LOGGER_URL` | `http://localhost:8090` | Task Logger URL |
| `AUDIT_LLAMAINDEX_URL` | `http://localhost:8002` | LlamaIndex service URL |
| `AUDIT_GKG_URL` | `http://localhost:8003` | GKG service URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `AUDIT_TIMEOUT_MULTIPLIER` | `1.0` | Global timeout multiplier |
| `AUDIT_QUALITY_THRESHOLD` | `70` | Minimum quality score to pass |
| `AUDIT_OUTPUT_DIR` | `./audit-results` | Output directory |
| `AUDIT_CLEANUP` | `false` | Clean up artifacts after run |
| `AUDIT_VERBOSE` | `false` | Enable debug logging |
