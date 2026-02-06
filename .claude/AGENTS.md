# Claude Code Custom Agents - Best Practices

## Quick Reference

All agents stored in `.claude/agents/` as Markdown with YAML frontmatter.

```yaml
---
name: agent-name                  # Required: lowercase, hyphens
description: "Use when..."        # Required: 2-3 sentences with examples
model: opus                       # opus | sonnet | haiku | inherit
memory: project                   # user | project | local
tools: Read, Glob, Grep          # Explicit allowlist (omit = inherit all)
color: yellow                     # UI identifier
---
```

## Frontmatter Fields

| Field | Options | Guidance |
|-------|---------|----------|
| **name** | kebab-case | `code-reviewer`, `test-writer`, `doc-generator` |
| **description** | 2-3 sentences | Start with "Use when..." or "Use proactively when..." Include examples |
| **model** | opus, sonnet, haiku, inherit | opus = complex analysis; sonnet = most tasks (default); haiku = simple |
| **memory** | user, project, local | **project** = team-shared (recommended); user = personal |
| **tools** | Specific list | Read-only: `Read, Glob, Grep`; Modifying: add `Edit, Write, Bash` |
| **color** | Any color | For visual identification in IDE |
| **permissionMode** | default | Always use `default` (ask user permission) |

## System Prompt Structure (Body)

Keep it simple and practical:

1. **Role Definition** (1 sentence)
   ```markdown
   You are an expert code reviewer specializing in...
   ```

2. **Core Responsibility** (1 sentence)
   ```markdown
   Your job is to identify code issues across clarity, maintainability, and bug prevention.
   ```

3. **Key Rules** (numbered if any)
   ```markdown
   **Key Rules**:
   1. Be specific: don't say "improve naming", say "rename X to Y"
   2. Provide exact code changes or before/after examples
   3. Omit sections with no findings
   ```

4. **Methodology** (numbered steps)
   ```markdown
   **Methodology**:
   1. [Step 1]
   2. [Step 2]
   3. [Step 3]
   ```

5. **Output Format** (if applicable)
   ```markdown
   **Output**:
   ## Section 1
   [content]

   ## Section 2
   [content]

   Omit sections with no findings.
   ```

6. **Memory Instructions** (if using memory)
   ```markdown
   **Update Memory After Each Task**:
   1. Record patterns you discover
   2. Note project conventions
   3. Keep MEMORY.md under 200 lines
   ```

## Memory Management

```
.claude/agent-memory/agent-name/
├── MEMORY.md          # Auto-loaded (first 200 lines) + links to topics
├── patterns.md        # Discovered patterns
└── conventions.md     # Project conventions
```

**MEMORY.md Format**:
- Keep under 200 lines
- Use links: `[Topic](topic.md)`
- Update after each task with learnings

## Common Agent Patterns

### Read-Only Analysis
```yaml
---
name: code-reviewer
description: "Use when reviewing code for quality, clarity, and bugs"
model: opus
memory: project
tools: Read, Glob, Grep
---
```

### Code Modification
```yaml
---
name: code-fixer
description: "Use when fixing bugs or refactoring code"
model: sonnet
memory: project
tools: Read, Glob, Grep, Edit, Write, Bash
---
```

### Simple Utility
```yaml
---
name: file-formatter
description: "Use when formatting files"
model: haiku
tools: Read, Glob, Edit, Bash
---
```

## Invocation Strategy

**Proactive** (auto-triggers):
```
This agent should be invoked proactively when you've written code and want review.
```

**Explicit** (manual):
```
Use the code-reviewer agent to analyze this code.
```

**Include Examples**:
```yaml
description: "Use this agent to review code...
Examples: after writing new features, before refactoring, code PR reviews"
```

## Quick Checklist

- [ ] Name: lowercase, hyphens only
- [ ] Description: 2-3 sentences, specific, with use cases
- [ ] Model: justified choice (opus/sonnet/haiku)
- [ ] Memory: `project` for team agents
- [ ] Tools: minimally scoped (not overpermissioned)
- [ ] Methodology: numbered, step-by-step
- [ ] Output: structured template with "omit empty sections"
- [ ] Memory: clear update instructions if enabled
- [ ] File: saved in `.claude/agents/`

## Common Mistakes

| ❌ Bad | ✅ Good |
|--------|---------|
| `description: "reviews code"` | `description: "reviews Python/TS code for clarity and bugs. Proactive after code changes"` |
| Model inheritance everywhere | Choose: opus (complex), sonnet (default), haiku (simple) |
| `tools: Read, Glob, Grep, Edit, Write, Bash, Task` | `tools: Read, Glob, Grep` (read-only) |
| No output format | Provide structured template with clear sections |
| No memory instructions | Explicit "Update memory after each task" section |
| 10-section system prompt | 5-6 focused sections max |

## Memory Location

```
User agents:        ~/.claude/agent-memory/agent-name/
Project agents:     .claude/agent-memory/agent-name/  (checked into git)
Local only:         .claude/agent-memory-local/agent-name/  (gitignored)
```

Use `memory: project` for team coordination and shared learnings.

## Agent Team Design Patterns

When creating agents intended to work as teammates in agent teams:

1. **Clear scope boundaries** — Agent description should state what it owns and what it does not
2. **Read-only when possible** — Reviewers and planners should use `tools: Read, Glob, Grep` only
3. **Structured output** — Teams work best when agents produce consistent, parseable output formats
4. **Memory: project** — All team agents should share project-scoped memory for cross-session learning
5. **No overlapping file ownership** — Two teammates should never edit the same file
6. **Team Collaboration section** — Every agent body should include collaboration instructions for team mode

### Team-Aware Agent Template

```yaml
---
name: my-teammate
description: "Use as a teammate for [specific purpose]. [Scope description]."
model: sonnet
memory: project
---
```

Body should include a `## Team Collaboration` section with:
- Scope boundaries (what this agent owns vs. doesn't)
- How to report findings to the team lead
- What to do when blocked or when cross-cutting issues are found

## References

- Claude Code official documentation
- Project code rules: [CLAUDE.md](CLAUDE.md)
- Agent files location: `.claude/agents/`
