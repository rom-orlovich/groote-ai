# Agent Manifest

## Source Routing
| Source | Event Pattern | Agent | Mode | Skills |
|--------|--------------|-------|------|--------|
| jira | issue_created, issue_updated, comment_created | jira-code-plan | default | jira-operations, discovery, knowledge-query |
| github | issues, issue_comment | github-issue-handler | default | github-operations, discovery, knowledge-query |
| github | pull_request.opened, pull_request.synchronize, pull_request.review_requested | github-pr-review | review | github-operations, verification, knowledge-query |
| github | pull_request_review_comment.created, issue_comment.created (on PR) | github-pr-review | improve | github-operations, slack-operations |
| github | issue_comment.created (on [PLAN] PR with "@agent approve") | github-pr-review | plan_approval | github-operations, multi-repo-plan |
| github | push | (skip) | - | Push events are not processed by agents |
| slack | message, app_mention | slack-inquiry | default | slack-operations, discovery, knowledge-graph, knowledge-query |

## Mode Detection for github-pr-review

**Review mode** (default): Triggered by PR opened, synchronize, or review_requested events. Agent reads the diff and posts a structured review comment.

**Improve mode**: Triggered by PR comments or review comments containing action keywords: `improve`, `fix`, `update`, `refactor`, `change`, `implement`, `address`. Agent checks out the PR branch, makes requested changes, commits, pushes, and posts a summary comment.

**Plan approval mode**: Triggered by `issue_comment.created` on a PR whose title starts with `[PLAN]` AND the comment contains `@agent approve`. Agent loads the plan, delegates to brain for team execution.

To detect mode from `issue_comment.created` on a PR:
1. Check if the comment body contains action keywords above
2. Check if `source_metadata.pr_number` is present (comment is on a PR, not an issue)
3. If both conditions met → improve mode
4. Otherwise → route to github-issue-handler

## Agent Selection by Source

- **jira** -> `jira-code-plan`
- **github** + issues/issue_comment -> `github-issue-handler`
- **github** + pull_request/pull_request_review_comment -> `github-pr-review`
- **github** + push -> Do not process (no agent assigned)
- **slack** -> `slack-inquiry`
- **unknown** -> `brain` (fallback)

## Task-Type Routing (internal delegation)
| Task Type | Agent | Skills |
|-----------|-------|--------|
| discovery, analysis | planning | discovery, github-operations, knowledge-graph, knowledge-query |
| research, knowledge | knowledge-researcher | knowledge-graph, knowledge-query, discovery |
| implementation | executor | testing, code-refactoring, github-operations, knowledge-query |
| verification | verifier | verification, testing |
| cross-service | service-integrator | github-operations, jira-operations, slack-operations |

## Complex/Ambiguous Tasks -> brain
Read ~/.claude/agents/brain.md for team creation and multi-agent orchestration.
