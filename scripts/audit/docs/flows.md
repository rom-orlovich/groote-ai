# Audit Framework - Flows

## Process Flows

### Audit Run Orchestration

```
[CLI] -> python -m scripts.audit --flow all
                    |
            [Parse Arguments]
                    |
            [Load AuditConfig]
                    |
            [Create AuditClient]
                    |
         [Check Prerequisites]
              |            |
         [Unhealthy]   [All Healthy]
              |            |
         [Exit 1]    [Start RedisEventMonitor]
                           |
                   [Resolve Flow IDs]
                           |
               [For Each Flow in Registry]
                           |
                    [flow.run()]
                           |
                 [Build FlowReport]
                           |
                [Optional: Cleanup]
                           |
              [Generate AuditReport]
                           |
             [Print Terminal Report]
                           |
              [Save JSON + TXT Reports]
                           |
                    [Exit 0 or 1]
```

**Processing Steps:**
1. Parse CLI arguments (flow IDs, timeouts, output dir)
2. Load AuditConfig from environment variables
3. Create AuditClient with httpx + redis connections
4. Check prerequisites: API Gateway, Dashboard API, Task Logger health
5. Start RedisEventMonitor on `task_events` stream
6. Resolve flow aliases to individual flow IDs
7. Execute each flow sequentially via flow.run()
8. Build FlowReport from each FlowResult
9. Run optional cleanup on each flow
10. Generate AuditReport with pass/fail counts and average quality
11. Print terminal report and save JSON/TXT to output directory

### BaseFlow Execution Lifecycle

```
[flow.run()] -> [Clear source events]
                        |
                  [trigger()]
                        |
               [TriggerResult returned]
                        |
          [_discover_task_id()]
                   |
          [Wait for webhook:task_created]
                   |
          [_wait_for_completion()]
                   |
          [Wait for task:completed]
                   |
          [_wait_for_response_posted()]
                   |
          [Wait for task:response_posted]
                   |
          [_extract_conversation_id()]
                   |
          [_run_component_audit()]
                   |
       [10 component checks executed]
                   |
          [_run_quality_evaluation()]
                   |
       [10 scoring dimensions evaluated]
                   |
          [_save_evidence()]
                   |
       [Events, components, quality saved]
                   |
          [Return FlowResult]
```

**Processing Steps:**
1. Clear stale source events from previous flows
2. Fire real webhook trigger via platform-specific Trigger class
3. Discover task_id by waiting for `webhook:task_created` event on Redis stream
4. Wait for `task:completed` event (up to 600s * multiplier)
5. Wait for `task:response_posted` event (up to 30s * multiplier)
6. Extract conversation_id from `task:context_built` event
7. Run full 10-component audit via ComponentMonitor
8. Run quality evaluation via QualityEvaluator (10 dimensions)
9. Save all evidence (events, components, quality) to JSON files
10. Return FlowResult with pass/fail, quality score, duration

### Slack Trigger Flow

```
[SlackTrigger] -> [Build event_callback payload]
                          |
                  [Generate HMAC signature]
                          |
                  [POST /webhooks/slack]
                          |
              [API Gateway validates + queues]
                          |
                  [Return TriggerResult]
                     platform: "slack"
                     flow_id: "slack:{channel}:{ts}"
```

**Processing Steps:**
1. Generate unique event timestamp and event ID
2. Build Slack `event_callback` payload with channel, user, text
3. Sign payload with HMAC-SHA256 using `SLACK_SIGNING_SECRET`
4. POST to API Gateway `/webhooks/slack` endpoint
5. Return TriggerResult with platform, artifact_id, flow_id

### Jira Trigger Flow (New Ticket)

```
[JiraTrigger] -> [POST to Jira API service]
                         |
                 [Create ticket via /api/v1/issues]
                         |
                 [Optionally add labels]
                         |
                 [Return TriggerResult]
                    platform: "jira"
                    flow_id: "jira:{issue_key}"
```

**Processing Steps:**
1. POST to Jira API service to create ticket with summary, description
2. Optionally PUT labels (e.g., `ai-agent`) on the created ticket
3. Return TriggerResult with issue key and flow_id

### Jira Trigger Flow (Existing Ticket)

```
[JiraTrigger] -> [GET existing ticket from Jira API]
                         |
                 [Build jira:issue_created webhook payload]
                         |
                 [Clear Redis dedup key]
                         |
                 [POST /webhooks/jira to API Gateway]
                         |
                 [Return TriggerResult]
```

**Processing Steps:**
1. Fetch existing ticket data from Jira API service
2. Build `jira:issue_created` webhook payload from ticket fields
3. Clear Redis dedup key to allow reprocessing
4. POST webhook payload directly to API Gateway
5. Return TriggerResult with issue key and flow_id

### GitHub Trigger Flow

```
[GitHubTrigger] -> [POST to GitHub API service]
                           |
              [Create issue/PR/comment via /api/v1/repos/...]
                           |
                   [Return TriggerResult]
                      platform: "github"
                      flow_id: "github:{owner}/{repo}#{number}"
```

**Processing Steps:**
1. POST to GitHub API service to create issue, PR comment, or branch+PR
2. Parse response for number/ID and html_url
3. Return TriggerResult with artifact_id and flow_id

### Quality Evaluation Flow

```
[QualityEvaluator] -> [Get events for task_id]
                              |
                      [Get tool calls for task_id]
                              |
                    [Run 10 scoring functions]
                              |
         [score_routing]           [score_tool_efficiency]
         [score_knowledge]         [score_knowledge_first]
         [score_completeness]      [score_relevance]
         [score_content_quality]   [score_delivery]
         [score_execution]         [score_errors]
                              |
                    [Calculate weighted average]
                              |
                    [Check critical dimensions]
                         |           |
                   [Any < 50]   [All >= 50]
                      |             |
                  [Force FAIL]  [Check threshold]
                                    |
                           [Return QualityReport]
```

**Processing Steps:**
1. Retrieve all events and tool calls for the task from Redis monitor
2. Run 10 independent scoring functions with events and FlowCriteria
3. Calculate weighted average across all dimensions
4. Check critical dimensions (Routing Accuracy, Content Quality) -- if any scores below 50, force fail
5. Generate improvement suggestions for low-scoring dimensions
6. Return QualityReport with overall score, pass/fail, and dimension breakdown

### Component Audit Flow

```
[ComponentMonitor] -> [full_component_audit()]
                              |
            [check_api_gateway]     -> response:immediate + webhook:task_created
            [check_redis_queue]     -> webhook:task_created + event count
            [check_agent_engine]    -> task:started event
            [check_task_routing]    -> task:created + correct agent
            [check_conversation_bridge] -> task:context_built + Dashboard API
            [check_mcp_servers]     -> tool calls + no critical errors
            [check_knowledge_layer] -> knowledge tool calls (optional)
            [check_response_poster] -> task:response_posted event
            [check_dashboard_api]   -> conversation messages exist
            [check_task_logger]     -> task logs available
                              |
                    [Return 10 ComponentStatus results]
                    [Each: name, status (healthy/degraded/failed), checks]
```

**Processing Steps:**
1. Run 10 component checks sequentially against the task_id
2. Each check queries Redis events and/or service APIs
3. Derive status: healthy (all pass), degraded (some pass), failed (none pass)
4. Return list of ComponentStatus with detailed check results

### Report Generation Flow

```
[ReportGenerator] -> [generate_terminal()]
                             |
                   [For each FlowReport]
                             |
              [Flow status, components, checkpoints]
              [Quality score + dimension breakdown]
              [Suggestions and error details]
                             |
                   [Summary: pass/fail/avg quality]
                             |
                   [save() -> report.json + report.txt]
```

**Processing Steps:**
1. Build ANSI-colored terminal output with flow results
2. Show component health status for each flow
3. Show quality score with per-dimension breakdown
4. Print summary with pass/fail counts and average quality
5. Save JSON report (machine-readable) and TXT report to output directory
