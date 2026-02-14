# Slack Response Templates

Templates for posting responses back to Slack after completing tasks.

## Task Completion Template

### Simple Completion

```markdown
## ✅ Task Complete

**Task ID:** `{task_id}`
**Summary:** {summary}

### Results

{results}

### Next Steps

{next_steps}
```

**MCP Tool:**

```json
{
  "tool": "slack:send_slack_message",
  "arguments": {
    "channel": "{channel_id}",
    "thread_ts": "{thread_ts}",
    "text": "{formatted_markdown}"
  }
}
```

### Rich Formatting (Blocks)

```json
{
  "tool": "slack:send_slack_message",
  "arguments": {
    "channel": "{channel_id}",
    "thread_ts": "{thread_ts}",
    "blocks": [
      {
        "type": "header",
        "text": {
          "type": "plain_text",
          "text": "✅ Task Complete"
        }
      },
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*Task ID:* `{task_id}`\n*Summary:* {summary}"
        }
      },
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*Results:*\n{results}"
        }
      }
    ]
  }
}
```

## Job Notification Templates

### Job Start

```markdown
🚀 _Job Started_

_Source:_ {source}
_Command:_ {command}
_Task ID:_ `{task_id}`
_Agent:_ {agent}
```

### Job Complete (Success)

```markdown
✅ _Task Completed_

_Task ID:_ `{task_id}`
_Summary:_ {summary}
_Cost:_ ${cost}
_Duration:_ {duration}
```

### Job Complete (Failure)

```markdown
❌ _Task Failed_

_Task ID:_ `{task_id}`
_Error:_ {error_message}
_Details:_ {error_details}
```

## Code Question Response Template

````markdown
## Analysis

{answer}

### Code Reference

```{language}
{code_snippet}
```
````

### Additional Context

{additional_context}

````

## Approval Request Template

```json
{
  "tool": "slack:send_slack_message",
  "arguments": {
    "channel": "{channel_id}",
    "blocks": [
      {
        "type": "header",
        "text": {
          "type": "plain_text",
          "text": "📋 Plan Ready for Approval"
        }
      },
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*{title}*\n\n🎫 Ticket: `{ticket_id}`\n🔗 <{pr_url}|View Draft PR #{pr_number}>"
        }
      },
      {
        "type": "actions",
        "elements": [
          {
            "type": "button",
            "text": {"type": "plain_text", "text": "✅ Approve"},
            "style": "primary",
            "action_id": "approve_plan"
          },
          {
            "type": "button",
            "text": {"type": "plain_text", "text": "❌ Reject"},
            "style": "danger",
            "action_id": "reject_plan"
          }
        ]
      }
    ]
  }
}
````

## Error Response Template

```markdown
## ❌ Task Failed

**Task ID:** `{task_id}`
**Error:** {error_message}

### Details

{error_details}

### Next Steps

{troubleshooting_steps}
```

## Cross-Platform Notification Templates

These templates are used by non-Slack agents to send Slack notifications after completing their primary platform action.

### GitHub Issue Processed

```markdown
*GitHub Issue Processed*

*Issue:* <{issue_url}|#{issue_number} {issue_title}>
*Repo:* `{repo}`
*Intent:* {bug fix | feature request | question}
*Action:* {what was done}
```

### PR Review Complete

```markdown
*PR Review Complete*

*PR:* <{pr_url}|#{pr_number} {pr_title}>
*Repo:* `{repo}`
*Verdict:* {Approve | Request Changes | Comment}
*Summary:* {one-line summary of key findings}
```

### Jira Task Complete

Use `ticket_url` from the task metadata (e.g., `https://company.atlassian.net/browse/KAN-18`). Never hardcode or guess the Jira domain.

```markdown
*Jira Task Analyzed*

*Ticket:* <{ticket_url}|{ticket_key} — {ticket_summary}>
*Scope:* {small | medium | large}
*Action:* {what was done}
*Status:* {status or next steps}
```

### Error / Failure Notification

```markdown
*Task Failed*

*Source:* {github | jira | slack}
*Reference:* {issue/ticket/thread link}
*Error:* {error_message}
*Details:* {brief description of what went wrong}
```

**MCP Tool for all notifications:**

```json
{
  "tool": "slack:send_slack_message",
  "arguments": {
    "channel": "{notification_channel from source_metadata or default}",
    "text": "{formatted_markdown}"
  }
}
```

Notification failures are best-effort — log the error but do not fail the primary task.

## Best Practices

1. **Always reply in thread** - Use `thread_ts` from task metadata
2. **Use markdown formatting** - Makes messages readable
3. **Include task context** - Task ID, summary, results
4. **Use appropriate emoji** - ✅ success, ❌ error, ⚠️ warning
5. **Keep messages concise** - Focus on key information
6. **Use blocks for rich formatting** - When interactive elements needed
7. **Mention users when needed** - Use `<@U123456>` format
