---
name: multi-repo-plan
description: Creates per-repo implementation plans and submits them as Draft PRs for human approval
---

# Multi-Repo Planning Skill

Use this skill when a task affects multiple repositories (identified via Knowledge Context).

## When to Use

- Knowledge Context identifies 2+ affected repos
- Task requires code changes (not just inquiry/analysis)
- Task source is Jira ticket or GitHub issue (not Slack question)

## Workflow

### 1. Analyze Knowledge Context

From the `## Affected Repos` and `## Relevant Code` sections:
- Identify which repos need changes
- Map file paths to specific changes needed
- Determine dependencies between repos (e.g., API change in backend requires frontend update)

### 2. Create Per-Repo Sub-Plans

For each affected repository, create a detailed sub-plan:

```
### Repo: {owner}/{repo}
**Local path**: /data/repos/{org_id}/{repo}

#### Files to Change
- `{file_path}` (L{start}-L{end}): {specific change}

#### Approach
{Step-by-step implementation approach}

#### Tests
- {test file}: {what to test}

#### Risks
- {risk}: {mitigation}
```

### 3. Create Plan PR Per Repo

For each affected repository:

1. Get the main branch SHA:
   ```
   github:get_branch_sha(owner, repo, "main")
   ```

2. Create a plan branch:
   ```
   github:create_branch(owner, repo, "plan/{task-id}", sha)
   ```

3. Write the plan file:
   ```
   github:create_or_update_file(
     owner, repo,
     "PLAN.md",
     plan_content,
     "[PLAN] {task title}",
     "plan/{task-id}"
   )
   ```

4. Create a draft PR:
   ```
   github:create_pull_request(
     owner, repo,
     "[PLAN] {task title}",
     "plan/{task-id}",
     "main",
     plan_body,
     draft=true
   )
   ```

### 4. Notify Human

After creating all plan PRs:

**Slack notification** (via `slack:send_slack_message`):
```markdown
*Multi-Repo Plan Ready for Review*

*Task:* {task title}
*Source:* {source} ({artifact link})

*Plan PRs:*
{for each repo}
- <{pr_url}|{owner}/{repo} #{pr_number}>
{end for}

Review each plan PR and comment `@agent approve` to proceed with implementation.
```

**Jira comment** (if source is Jira, via `jira:add_jira_comment`):
```markdown
h3. Multi-Repo Plan Created

Plan PRs for review:
{for each repo}
* [{owner}/{repo} #{pr_number}|{pr_url}]
{end for}

Comment "@agent approve" on each plan PR to proceed with implementation.
```

### 5. Plan Content Template

Each PLAN.md should follow this structure:

```markdown
# Implementation Plan: {task title}

## Task Reference
- Source: {jira ticket / github issue URL}
- Task ID: {task-id}

## Summary
{1-2 sentences describing the change}

## Changes

### {file_path}
**Current behavior**: {what it does now}
**New behavior**: {what it should do}
**Lines affected**: L{start}-L{end}

\`\`\`{language}
// Proposed code change
{code}
\`\`\`

### {file_path_2}
...

## Testing Strategy
- {test approach}

## Risks
- {risk}: {mitigation}

## Dependencies
- Depends on: {other repo plans if any}
- Blocks: {what this unblocks}
```
