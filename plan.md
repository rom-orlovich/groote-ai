# Agent Teams Configuration Plan for Groote AI

## Context

Claude Code has a built-in agent-teams feature that coordinates multiple Claude Code sessions as a team. Currently, Groote AI doesn't leverage this — the agent-engine runs single sessions. This plan configures the project at every level (root, agent-engine, per-service) to support agent teams natively.

**What agent-teams gives us out of the box:**
- Team lead + teammates as independent Claude Code sessions
- Shared task list with dependencies
- Inter-agent mailbox messaging
- Plan approval workflow (lead approves teammate plans)
- Delegate mode (lead only orchestrates)

**What we need to do:** Enable the feature, define agents that work well as teammates, and give each service enough CLAUDE.md context so teammates understand the architecture.

---

## 1. Enable Agent Teams in Settings

### File: `.claude/settings.local.json`

Add the experimental flag + teammate display mode:

```json
{
  "permissions": {
    "allow": [
      "mcp__plugin_playwright_playwright__*",
      "WebSearch",
      "WebFetch(domain:vitest.dev)",
      "Write(*)",
      "Edit(*)",
      "Read(*)"
    ]
  },
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "teammateMode": "in-process"
}
```

---

## 2. Root-Level Agents (`.claude/agents/`)

These are the team roles available when working from the project root. They replace the single `code-review-expert.md` with a full team roster.

### Keep: `.claude/agents/code-review-expert.md` (already exists, good as-is)

### Create: `.claude/agents/brain.md` (Team Lead)

Root-level orchestrator that can create and lead agent teams. Understands the full microservices architecture and delegates to specialized teammates.

```yaml
---
name: brain
description: "Central orchestrator and team lead for Groote AI. Use when coordinating complex multi-service tasks, creating agent teams, or routing work across the system. This agent should lead teams for features spanning multiple services."
model: opus
memory: project
---
```

Body: Knows the full service map, creates teams for complex tasks, decomposes work into per-service tasks, synthesizes results. Includes the routing table from agent-engine's brain but at the project level.

### Create: `.claude/agents/planner.md` (Teammate: Architecture & Planning)

```yaml
---
name: planner
description: "Use as a teammate for code discovery, architecture analysis, and implementation planning. Reads code, identifies affected files, and creates step-by-step plans."
model: opus
memory: project
tools: Read, Glob, Grep
---
```

Body: Read-only agent. Explores codebase, creates PLAN.md, identifies risks. Focuses on YOUR assigned service/scope only — don't duplicate other teammates' work.

### Create: `.claude/agents/implementer.md` (Teammate: Code Changes)

```yaml
---
name: implementer
description: "Use as a teammate for implementing code changes following TDD. Owns specific files and services — never edits files assigned to other teammates."
model: sonnet
memory: project
skills:
  - testing
  - code-refactoring
---
```

Body: TDD workflow (Red → Green → Refactor). Follows project rules (300 line max, no `any`, no comments, async/await). Commits with conventional format.

### Create: `.claude/agents/reviewer.md` (Teammate: Quality & Security)

```yaml
---
name: reviewer
description: "Use as a teammate focused on code review, security audit, test coverage validation, and performance analysis. Reports findings with severity ratings."
model: opus
memory: project
tools: Read, Glob, Grep, Bash
---
```

Body: Review methodology (security, performance, test coverage, code quality). Structured output with severity ratings. Challenges other teammates' implementations.

### Create: `.claude/agents/debugger.md` (Teammate: Investigation & Debugging)

```yaml
---
name: debugger
description: "Use as a teammate for investigating bugs, testing hypotheses, and root cause analysis. Can run tests, read logs, and reproduce issues."
model: opus
memory: project
---
```

Body: Investigates with competing hypotheses. Shares findings with teammates to disprove/confirm theories. Focuses on evidence-based debugging.

### Create: `.claude/agents/service-specialist.md` (Teammate: Per-Service Expert)

```yaml
---
name: service-specialist
description: "Use as a teammate that owns a specific service (api-gateway, dashboard-api, external-dashboard, etc.). Deep knowledge of one service's internals."
model: sonnet
memory: project
---
```

Body: When spawned, the lead tells it which service to own. Reads that service's CLAUDE.md, understands its patterns, makes changes only within its directory.

---

## 3. Agent-Engine Agents Updates (`agent-engine/.claude/agents/`)

The agent-engine agents are used when Claude Code runs **inside** the agent-engine container. They need team-awareness instructions added.

### Update ALL 9 agent files — add team awareness section

Add to each agent's body (after existing content):

```markdown
## Team Collaboration

When working as part of an agent team:
- You receive context from the team lead in your spawn prompt
- Focus exclusively on YOUR assigned scope — do not edit files owned by other teammates
- Share important discoveries with your team lead when you complete your task
- If you find something that affects another teammate's work, mention it in your result
- When blocked, report what you need rather than working around it
```

### Update: `agent-engine/.claude/agents/brain.md`

Enhance to support team creation. Add after existing routing table:

```markdown
## Agent Team Mode

For complex tasks that benefit from parallel work, create an agent team:

**When to create a team:**
- GitHub issues labeled "feature" or involving multiple files/services
- PR reviews (spawn security, performance, and test coverage reviewers)
- Debugging tasks with unclear root cause (competing hypotheses)
- Jira tickets marked "AI-Fix" that span multiple modules

**Team creation pattern:**
1. Analyze the incoming task
2. Determine strategy: parallel_review, decomposed_feature, competing_hypotheses
3. Create a team with appropriate teammates from available agents
4. Assign each teammate a clear scope and file ownership
5. Require plan approval for implementation tasks
6. Wait for all teammates to complete
7. Synthesize results into a unified response

**Example team for a feature request:**
```
Create an agent team for this task. Spawn:
- A planner teammate to analyze the codebase and create an implementation plan. Require plan approval.
- An implementer teammate to write the code (after planner completes). Require plan approval.
- A reviewer teammate to verify quality and security (after implementer completes).
```

**Example team for PR review:**
```
Create an agent team to review this PR. Spawn:
- A security reviewer focused on auth, input validation, and secrets
- A performance reviewer checking for bottlenecks and resource leaks
- A test coverage reviewer validating test adequacy
Have them each review independently and share findings.
```
```

---

## 4. CLAUDE.md Updates Across Services

Each service's CLAUDE.md needs enough context so that when a teammate is spawned in that directory (or reads about it), they understand what they're working with.

### Update: Root `.claude/CLAUDE.md`

Add team instructions section:

```markdown
## Agent Teams

This project supports Claude Code agent teams. When working as a team:

- **Brain** is the team lead — it decomposes tasks and coordinates teammates
- Each teammate owns a specific service or concern (security, performance, etc.)
- Teammates MUST NOT edit files outside their assigned scope
- All teammates follow the same code standards above
- Use structured findings when reporting to the team lead

### Service Ownership for Teams

When assigning teammates to services, each teammate should `cd` into their service directory and read its CLAUDE.md:

| Service | Directory | Typical Teammate Role |
|---------|-----------|----------------------|
| API Gateway | `api-gateway/` | Webhook & routing changes |
| Agent Engine | `agent-engine/` | Task processing & CLI integration |
| Dashboard API | `dashboard-api/` | Backend API & WebSocket changes |
| External Dashboard | `external-dashboard/` | Frontend React changes |
| OAuth Service | `oauth-service/` | Auth flow changes |
| MCP Servers | `mcp-servers/` | Tool integration changes |
```

### Update: Per-service CLAUDE.md files (all 11 services)

Each service CLAUDE.md should already describe the service. Verify each has:
1. What the service does (1-2 sentences)
2. Key files and structure
3. How to run tests
4. How to run the service locally
5. Dependencies on other services

Files to check/update:
- `api-gateway/CLAUDE.md`
- `agent-engine/CLAUDE.md` (already detailed)
- `dashboard-api/CLAUDE.md`
- `external-dashboard/CLAUDE.md` (if exists, else create)
- `oauth-service/CLAUDE.md`
- `task-logger/CLAUDE.md`
- `mcp-servers/CLAUDE.md`
- `api-services/CLAUDE.md` (if exists)
- `gkg-service/CLAUDE.md`
- `llamaindex-service/CLAUDE.md`
- `indexer-worker/CLAUDE.md`

---

## 5. Agent-Engine `.claude/CLAUDE.md` (Inner CLAUDE.md)

This is what agents see when running inside the agent-engine container. Update to include team patterns:

Add section:

```markdown
## Agent Team Patterns

The Brain agent can create agent teams for complex tasks. When working as a teammate:

### Available Team Strategies

1. **parallel_review**: Multiple reviewers analyze different aspects simultaneously
2. **decomposed_feature**: Planning → Implementation → Verification pipeline
3. **competing_hypotheses**: Multiple agents investigate different theories
4. **cross_layer**: Each agent owns a different service/layer

### File Ownership Rules

- Each teammate is assigned specific files/directories
- NEVER edit files outside your assignment
- If you discover a needed change outside your scope, report it to the lead
- The lead resolves cross-cutting concerns after teammates complete
```

---

## 6. Root `.claude/AGENTS.md` Update

Already has good agent creation guidelines. Add a section for team-aware agents:

```markdown
## Agent Team Design Patterns

When creating agents intended to work as teammates:

1. **Clear scope boundaries** — Agent description should state what it owns and doesn't own
2. **Read-only when possible** — Reviewers and planners should use `tools: Read, Glob, Grep` only
3. **Structured output** — Teams work best when agents produce consistent, parseable output
4. **Memory: project** — All team agents should share project-scoped memory for cross-session learning
5. **No overlapping file ownership** — Two teammates should never edit the same file
```

---

## Summary of All Changes

### Files to Create (6 new agent definitions):
- `.claude/agents/brain.md`
- `.claude/agents/planner.md`
- `.claude/agents/implementer.md`
- `.claude/agents/reviewer.md`
- `.claude/agents/debugger.md`
- `.claude/agents/service-specialist.md`

### Files to Modify:
- `.claude/settings.local.json` — enable agent teams env var
- `.claude/CLAUDE.md` — add team instructions + service ownership table
- `.claude/AGENTS.md` — add team design patterns section
- `agent-engine/.claude/agents/brain.md` — add team creation patterns
- `agent-engine/.claude/agents/executor.md` — add team collaboration section
- `agent-engine/.claude/agents/planning.md` — add team collaboration section
- `agent-engine/.claude/agents/verifier.md` — add team collaboration section
- `agent-engine/.claude/agents/github-issue-handler.md` — add team collaboration section
- `agent-engine/.claude/agents/github-pr-review.md` — add team collaboration section
- `agent-engine/.claude/agents/jira-code-plan.md` — add team collaboration section
- `agent-engine/.claude/agents/slack-inquiry.md` — add team collaboration section
- `agent-engine/.claude/agents/service-integrator.md` — add team collaboration section
- `agent-engine/.claude/CLAUDE.md` — add team patterns section
- Per-service CLAUDE.md files — verify each has enough context for teammates

### No Python/TypeScript code changes needed.

---

## Verification

1. After enabling, start Claude Code from project root and ask: "Create an agent team to review the agent-engine architecture"
2. Verify teammates spawn and can read CLAUDE.md from their working directories
3. Test a parallel review: "Create a team to review PR #X with security, performance, and test reviewers"
4. Test decomposed feature: "Create a team to add [feature] — one planner, one implementer, one reviewer"
5. Verify teammates stay within their assigned scope and don't conflict on files
