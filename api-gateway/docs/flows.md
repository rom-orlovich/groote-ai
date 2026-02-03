# API Gateway - Flows

## Process Flows

### GitHub Webhook Flow

```
[GitHub] → POST /webhooks/github → [Middleware: Validate Signature]
                                           ↓
                               [Parse X-GitHub-Event header]
                                           ↓
                           [Extract metadata: owner, repo, number]
                                           ↓
                              [Check if event should process]
                                     ↓           ↓
                                 [Skip]     [Process]
                                   ↓             ↓
                              [200 OK]    [Create Task]
                                               ↓
                                    [Enqueue to Redis]
                                               ↓
                                       [202 Accepted]
                                               ↓
                                [Async: Add 👀 reaction]
```

**Processing Steps:**
1. Receive POST request with GitHub webhook payload
2. Middleware validates HMAC-SHA256 signature using `GITHUB_WEBHOOK_SECRET`
3. Parse `X-GitHub-Event` header to determine event type
4. Extract metadata: owner, repo, PR/issue number, labels
5. Check if event type and action are supported
6. Skip bot comments and unsupported events → Return 200 OK
7. Create task with extracted metadata and appropriate agent type
8. Enqueue task to Redis (`agent:tasks` list)
9. Return 202 Accepted with task_id
10. Async: Post 👀 reaction to acknowledge via github-api service

### Jira Webhook Flow

```
[Jira] → POST /webhooks/jira → [Middleware: Validate Signature]
                                          ↓
                                 [Parse Issue Data]
                                          ↓
                               [Check for AI-Fix label]
                                    ↓          ↓
                              [No Label]   [Has Label]
                                  ↓             ↓
                             [200 OK]     [Check Assignee]
                                               ↓
                                        [Create Task]
                                               ↓
                                    [Enqueue to Redis]
                                               ↓
                                       [202 Accepted]
```

**Processing Steps:**
1. Receive POST request with Jira webhook payload
2. Middleware validates signature using `JIRA_WEBHOOK_SECRET`
3. Parse issue data: key, summary, description, labels
4. Check if issue has "AI-Fix" label
5. Skip if no AI-Fix label → Return 200 OK
6. Check if assignee matches AI agent configuration
7. Create task with ticket metadata
8. Enqueue task to Redis for `jira-code-plan` agent
9. Return 202 Accepted with task_id

### Slack Webhook Flow

```
[Slack] → POST /webhooks/slack → [URL Verification Challenge?]
                                         ↓
                           [Yes: Return challenge value]
                           [No: Validate Signature]
                                         ↓
                              [Parse Event Data]
                                         ↓
                              [Check if from bot]
                                    ↓         ↓
                                [Bot]     [User]
                                  ↓           ↓
                             [200 OK]   [Create Task]
                                              ↓
                                   [Enqueue to Redis]
                                              ↓
                                        [200 OK]
```

**Processing Steps:**
1. Receive POST request from Slack Events API
2. Handle URL verification challenge if present
3. Validate signature using `SLACK_SIGNING_SECRET`
4. Parse event: type, user, channel, text, thread_ts
5. Skip bot messages → Return 200 OK
6. Create task with channel context and thread info
7. Enqueue task to Redis for `slack-inquiry` agent
8. Return 200 OK (Slack expects 200 for all responses)

### Sentry Webhook Flow

```
[Sentry] → POST /webhooks/sentry → [Middleware: Validate Signature]
                                            ↓
                                   [Parse Alert Data]
                                            ↓
                                 [Check Event Type]
                                      ↓         ↓
                               [Resolved]   [New/Regression]
                                   ↓              ↓
                              [200 OK]      [Create Task]
                                                  ↓
                                       [Enqueue to Redis]
                                                  ↓
                                          [202 Accepted]
```

**Processing Steps:**
1. Receive POST request with Sentry alert webhook
2. Middleware validates signature using `SENTRY_WEBHOOK_SECRET`
3. Parse alert: issue ID, project, event type, culprit
4. Skip resolved events → Return 200 OK
5. Create task with error context
6. Set high priority for regressions
7. Enqueue task to Redis for `sentry-error-handler` agent
8. Return 202 Accepted with task_id

### Loop Prevention Flow

```
[Incoming Webhook] → [Check Comment ID in Redis]
                              ↓
                    [Found in posted-comments?]
                         ↓           ↓
                      [Yes]        [No]
                        ↓            ↓
                   [200 OK]   [Check User Type]
                                    ↓
                              [Is Bot?]
                              ↓       ↓
                           [Yes]    [No]
                             ↓        ↓
                        [200 OK]  [Continue]
```

**Prevention Logic:**
1. When processing webhook, extract comment ID
2. Check if comment ID exists in Redis `posted-comments` set
3. If found → Skip processing (agent already processed this)
4. Check if user type is "Bot" or username matches known bots
5. If bot → Skip processing to avoid infinite loops
6. Otherwise → Continue with normal processing

## Response Flow

### Immediate Response (< 50ms)

All webhooks return response immediately after enqueue:
- External service doesn't timeout
- Task processing happens asynchronously
- Response includes task_id for tracking

### Visual Acknowledgment (< 100ms)

For GitHub webhooks, async acknowledgment:
1. Task enqueued → Response returned
2. Background: POST to github-api service
3. Add 👀 reaction to comment/issue
4. User sees immediate feedback

### Final Result (async)

After agent-engine completes:
- **Success**: Comment with results + cost
- **Failure**: 👎 reaction (no new comment to avoid noise)
