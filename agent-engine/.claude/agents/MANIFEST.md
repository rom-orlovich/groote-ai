# Agent Manifest

All incoming tasks are routed through the **brain** agent. The brain uses this manifest as a reference to decide which specialist agent to delegate to.

## Source Routing (Brain Reference)

| Source | Event Pattern | Target Agent | Mode |
|--------|--------------|-------|------|
| jira | issue_created, issue_updated, comment_created | jira-code-plan | default |
| github | issues, issue_comment (on issue) | github-issue-handler | default |
| github | pull_request.opened, pull_request.synchronize, pull_request.review_requested | github-pr-review | review |
| github | pull_request_review_comment.created, issue_comment (on PR with improve keyword) | github-pr-review | improve |
| github | issue_comment (on [PLAN] PR with approve command) | github-pr-review | plan_approval |
| github | push | (skip) | - |
| slack | message, app_mention | slack-inquiry | default |

## Mode Detection for github-pr-review

**Review mode** (default): Triggered by PR opened, synchronize, or review_requested events. Agent reads the diff and posts a structured review comment.

**Improve mode**: Triggered by PR comments or review comments containing action keywords from `Improve-Keywords` header field. Agent checks out the PR branch, makes requested changes, commits, pushes, and posts a summary comment.

**Plan approval mode**: Triggered by `issue_comment` on a PR whose title starts with `[PLAN]` AND the comment contains a bot mention + approve command (from `Bot-Mentions` and `Approve-Command` header fields). Agent loads the plan, delegates to brain for team execution.

## Task-Type Routing (internal delegation)

| Task Type | Agent | Skills |
|-----------|-------|--------|
| discovery, analysis | planning | discovery, github-operations, knowledge-graph, knowledge-query |
| research, knowledge | knowledge-researcher | knowledge-graph, knowledge-query, discovery |
| implementation | executor | testing, code-refactoring, github-operations, knowledge-query |
| verification | verifier | verification, testing |
| cross-service | service-integrator | github-operations, jira-operations, slack-operations |

## Complex/Ambiguous Tasks

The brain agent handles these directly or creates agent teams. See `~/.claude/agents/brain.md` for team creation and multi-agent orchestration strategies.
