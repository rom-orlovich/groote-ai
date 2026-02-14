# Groote AI - System Flows

## End-to-End System Flows

These flows show how requests move through the entire groote-ai system, from external trigger to platform response. For individual service flows, see per-service docs (e.g., `api-gateway/docs/flows.md`).

### Jira Comment Trigger

A user mentions the AI agent in a Jira comment, triggering analysis and response.

```
[User] -> Jira Comment (mentions @ai-agent)
                    |
[Jira] -> POST /webhooks/jira -> [API Gateway :8000]
                                        |
                                [Validate Signature]
                                        |
                              [Check ai-agent label]
                                   |          |
                             [No Label]   [Has Label]
                                 |             |
                            [200 OK]    [Check bot/dedup]
                                              |
                                    [Create Task in PostgreSQL]
                                              |
                                    [LPUSH agent:tasks in Redis]
                                              |
                                       [202 Accepted]
                                              |
                        [Agent Engine :8080 BRPOP agent:tasks]
                                              |
                               [Route to jira-code-plan agent]
                                              |
                        [Build context from Dashboard API conversation]
                                              |
                               [Execute via Claude/Cursor CLI]
                                       |            |
                            [MCP: knowledge_query]  [MCP: search_jira_tickets]
                            [Knowledge Graph MCP]   [Jira MCP :9002]
                            [:9005 -> KG :4000]     [-> Jira API :3002 -> Jira]
                                       |
                             [Generate response]
                                       |
                            [MCP: add_jira_comment]
                            [Jira MCP :9002 -> Jira API :3002 -> Jira]
                                       |
                          [task:response_posted event]
                                       |
                    [Redis pub/sub -> Dashboard API :5000]
                                       |
                    [WebSocket -> External Dashboard :3005]
                                       |
                    [Task Logger :8090 captures output]
```

**Key Checkpoints:**
1. Webhook received and validated within 50ms
2. Task created and queued in Redis
3. Agent Engine picks up task
4. Routed to correct agent (jira-code-plan)
5. Context built from conversation history
6. Knowledge tools queried before response
7. Response posted back to Jira via MCP
8. Dashboard updated in real-time via WebSocket

### GitHub PR Review

A PR is opened or a comment is added, triggering an automated code review.

```
[Developer] -> Opens PR / Adds PR Comment
                        |
[GitHub] -> POST /webhooks/github -> [API Gateway :8000]
                                            |
                                    [Validate HMAC-SHA256]
                                            |
                                    [Parse X-GitHub-Event]
                                            |
                                    [Extract owner, repo, PR#]
                                            |
                                    [Check bot / loop prevention]
                                          |           |
                                      [Skip]     [Process]
                                        |             |
                                   [200 OK]    [Create Task]
                                                     |
                                          [LPUSH agent:tasks]
                                                     |
                                              [202 Accepted]
                                                     |
                                        [Async: Add reaction]
                                        [GitHub MCP -> GitHub API -> GitHub]
                                                     |
                              [Agent Engine routes to github-pr-review]
                                                     |
                                         [Build conversation context]
                                                     |
                                     [Execute via Claude/Cursor CLI]
                                              |            |
                                   [MCP: knowledge_query]  [Read PR diff]
                                   [KG MCP :9005]          [GitHub MCP :9001]
                                              |
                                   [Generate code review]
                                              |
                                   [MCP: add_issue_comment]
                                   [GitHub MCP -> GitHub API -> GitHub]
                                              |
                                [task:response_posted event]
                                              |
                        [Dashboard + Task Logger updated]
```

**Key Checkpoints:**
1. Webhook signature validated
2. Event type and action filtered (opened, synchronize, reopened)
3. Bot comments skipped (loop prevention)
4. Task routed to github-pr-review agent
5. PR diff analyzed via GitHub MCP tools
6. Knowledge layer consulted for codebase context
7. Review comment posted back to PR

### Slack Knowledge Query

A user mentions the agent in Slack asking about a codebase.

```
[User] -> @agent "What does the auth module do?"
                        |
[Slack] -> POST /webhooks/slack -> [API Gateway :8000]
                                          |
                             [URL Verification? -> Return challenge]
                                          |
                                [Validate X-Slack-Signature]
                                          |
                                  [Check if from bot]
                                       |         |
                                   [Bot]      [User]
                                     |           |
                                [200 OK]   [Create Task]
                                                 |
                                      [LPUSH agent:tasks]
                                                 |
                                           [200 OK]
                                                 |
                          [Agent Engine routes to slack-inquiry]
                                                 |
                                      [Build conversation context]
                                      [Check for thread history]
                                                 |
                                  [Execute via Claude/Cursor CLI]
                                          |            |
                               [MCP: knowledge_query]  [MCP: code_search]
                               [KG MCP :9005]          [LlamaIndex MCP :9006]
                               [-> KG :4000]           [-> LlamaIndex :8002]
                                          |
                                [Generate answer with citations]
                                          |
                               [MCP: send_slack_message]
                               [Slack MCP :9003 -> Slack API :3003 -> Slack]
                                          |
                            [task:response_posted event]
                                          |
                      [Dashboard + Task Logger updated]
```

**Key Checkpoints:**
1. Slack signature validated
2. Bot messages filtered out
3. Task routed to slack-inquiry agent
4. Knowledge tools queried (knowledge_query, code_search)
5. Response references target repository, not groote-ai internals
6. Response posted back to Slack channel/thread via MCP

### Dashboard Real-Time Updates

How task status changes propagate to the dashboard UI in real-time.

```
[Agent Engine] -> Task status change
                        |
              [Redis PUBLISH task:{task_id}]
                        |
              [Redis Pub/Sub Channel]
                  |              |
    [Dashboard API :5000]  [Task Logger :8090]
           |                      |
    [WebSocket broadcast]   [Write to log file]
           |
    [External Dashboard :3005]
           |
    [React state update via useEffect]
           |
    [UI renders new status/output]
```

**Event Types Published:**
- `task:created` - Task created from webhook
- `task:started` - Agent Engine picked up task
- `task:context_built` - Conversation context assembled
- `task:tool_call` - Agent called an MCP tool
- `task:tool_result` - MCP tool returned result
- `task:output` - Agent produced output text
- `task:response_posted` - Response posted to platform
- `task:completed` - Task finished (success/failure)

### Full Pipeline (Webhook to Response)

Summary of the complete system flow applicable to all trigger types.

```
[External Service]
        |
        | POST /webhooks/{source}
        v
[API Gateway :8000]
        |
        | 1. Validate signature (HMAC-SHA256)
        | 2. Check loop prevention (Redis)
        | 3. Parse event metadata
        | 4. Create task (PostgreSQL)
        | 5. Enqueue task (Redis LPUSH agent:tasks)
        | 6. Return 200/202 (< 50ms)
        v
[Redis Queue: agent:tasks]
        |
        | BRPOP
        v
[Agent Engine :8080]
        |
        | 1. Route to specialized agent
        | 2. Build conversation context (Dashboard API)
        | 3. Execute CLI (Claude/Cursor)
        | 4. Stream output (Redis pub/sub)
        v
[MCP Tool Calls via SSE]
        |
        +---> [GitHub MCP :9001] -> [GitHub API :3001] -> [GitHub]
        +---> [Jira MCP :9002]   -> [Jira API :3002]   -> [Jira]
        +---> [Slack MCP :9003]  -> [Slack API :3003]   -> [Slack]
        +---> [KG MCP :9005]    -> [Knowledge Graph :4000]
        +---> [LlamaIndex MCP :9006] -> [LlamaIndex :8002] (optional)
        +---> [GKG MCP :9007]   -> [GKG Service :8003] (optional)
        |
        v
[Response Posted via MCP]
        |
        | task:response_posted
        v
[Redis Pub/Sub]
   |          |
   v          v
[Dashboard API :5000]    [Task Logger :8090]
   |                            |
   | WebSocket                  | File write
   v                            v
[Dashboard :3005]         [Log files]
```

**Timing Expectations:**
- Webhook to HTTP response: < 50ms
- Task creation to agent pickup: < 5s
- Agent execution: 30s - 600s (depending on task complexity)
- Response posting: < 30s after execution completes
