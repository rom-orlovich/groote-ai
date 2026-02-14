# Audit Framework - Features

## Overview

End-to-end system validation framework that fires real webhooks through the groote-ai pipeline and evaluates every component's response with multi-dimensional quality scoring.

## Core Features

### Flow Execution

Runs 8 registered audit flows that exercise the full system pipeline. Each flow fires a real trigger, waits for task completion, verifies component health, and evaluates response quality.

**Registered Flows:**

| ID | Name | Category | Trigger | Expected Agent |
|----|------|----------|---------|----------------|
| f01 | Slack Knowledge | Slack | Slack message | slack-inquiry |
| f02 | Jira Code Plan | Jira | New Jira ticket | jira-code-plan |
| f04 | GitHub PR Review | GitHub | PR comment | github-pr-review |
| f05 | Jira Comment | Jira | Jira comment | jira-code-plan |
| f06 | Full Chain | Jira | Cross-platform chain | jira-code-plan |
| f07 | Knowledge Health | Knowledge | Knowledge service check | slack-inquiry |
| f08 | Slack Multi-Repo | Slack | Multi-repo question | slack-inquiry |
| f09 | Plan Approval | Jira | Plan approval workflow | jira-code-plan |

### Category Aliases

Run flows by category instead of individual IDs:

| Alias | Flows |
|-------|-------|
| `all` | f01, f02, f03, f04, f05, f06, f07, f08, f09 |
| `slack` | f01, f08 |
| `jira` | f02, f05, f09 |
| `github` | f03, f04 |
| `chain` | f06 |
| `knowledge` | f07 |

### Real Webhook Triggers

Three trigger types fire actual HTTP requests through the API Gateway with proper signatures and payloads.

**Trigger Types:**
- `SlackTrigger` - HMAC-signed Slack event payloads via POST /webhooks/slack
- `JiraTrigger` - Jira ticket/comment creation via Jira API service, then webhook
- `GitHubTrigger` - GitHub issue/PR/comment creation via GitHub API service

### Quality Evaluation

10-dimension weighted scoring system evaluates response quality. Two dimensions (Routing Accuracy, Content Quality) are critical -- scoring below 50 forces a fail regardless of overall score.

**Scoring Dimensions:**

| Dimension | Weight | Measures |
|-----------|--------|----------|
| Routing Accuracy | 15 | Correct agent assigned to task |
| Content Quality | 15 | Output references target repo, no negative patterns, meets min length |
| Tool Efficiency | 10 | Required tools called without excessive redundancy |
| Knowledge Utilization | 10 | Knowledge layer tools used when applicable |
| Knowledge First | 10 | Knowledge tools called before domain action tools |
| Response Completeness | 10 | Output matches required patterns and length |
| Response Relevance | 10 | Output contains domain-specific terminology |
| Delivery Success | 10 | Response posted back via MCP to originating platform |
| Execution Metrics | 5 | Task completed within time bounds |
| Error Freedom | 5 | No errors in event stream |

### Component Monitoring

Verifies 10 pipeline components participated correctly during each flow execution.

**Monitored Components:**

| Component | Verification Method |
|-----------|-------------------|
| api-gateway | `response:immediate` and `webhook:task_created` events |
| redis-queue | `webhook:task_created` event with task count |
| agent-engine | `task:started` event |
| task-routing | `task:created` event with correct assigned_agent |
| conversation-bridge | `task:context_built` event + Dashboard API conversation lookup |
| mcp-servers | Tool call count + no critical MCP errors |
| knowledge-layer | Knowledge tool calls and results (optional) |
| response-poster | `task:response_posted` event |
| dashboard-api | Conversation messages exist with system/assistant roles |
| task-logger | Task logs available via Task Logger API |

### Redis Event Monitoring

Real-time listener on the `task_events` Redis stream. Supports waiting for specific events by task_id or source with configurable timeouts.

**Capabilities:**
- Continuous XREAD on `task_events` stream
- Event dispatching by task_id and source
- Async waiters with timeout support
- Source event epoch tracking for stale event filtering
- Tool call extraction from event stream

### Evidence Collection

Saves audit artifacts as structured JSON files for post-run analysis.

**Collected Evidence:**
- `events.json` - All Redis stream events for the flow
- `component_status.json` - Component health check results
- `quality_report.json` - Quality dimension breakdown
- `report.json` - Full audit report (machine-readable)
- `report.txt` - Terminal-formatted report with ANSI codes

### Report Generation

Produces both terminal output (ANSI-colored) and JSON reports.

**Report Contents:**
- Per-flow pass/fail status
- Component health breakdown
- Quality score with dimension details
- Suggestions for improvement
- Duration and evidence paths
- Summary with pass/fail counts and average quality

### Checkpoint Runner

Sequential checkpoint execution with critical/non-critical distinction. If a critical checkpoint fails, subsequent checkpoints are skipped.

**Checkpoint Statuses:**
- `PENDING` - Not yet executed
- `PASSED` - Completed successfully
- `FAILED` - Threw exception
- `SKIPPED` - Skipped due to prior critical failure

## CLI Interface

| Flag | Default | Description |
|------|---------|-------------|
| `--flow` | `all` | Flows to run (IDs or aliases) |
| `--timeout-multiplier` | `1.0` | Global timeout scaling factor |
| `--output-dir` | `./audit-results` | Evidence output directory |
| `--cleanup` | `false` | Clean up audit artifacts after run |
| `--verbose` | `false` | Enable DEBUG-level logging |
| `--quality-threshold` | `70` | Minimum quality score to pass |
| `--slack-channel` | config | Override Slack channel |
| `--github-owner` | config | Override GitHub owner |
| `--github-repo` | config | Override GitHub repo |
| `--jira-project` | config | Override Jira project |
| `--ticket` | none | Use existing Jira ticket instead of creating new |
