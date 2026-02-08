# Agent Engine

Scalable task execution engine (port 8080-8089). Consumes tasks from Redis queue, executes via CLI providers (Claude/Cursor), and posts results back.

## CLI Provider Selection

Set via `CLI_PROVIDER` environment variable:

- `claude`: `claude -p --output-format stream-json`
- `cursor`: `agent chat --print --output-format json-stream`

## Agent Routing

**IMPORTANT**: Brain routes tasks based on source and task type:

**Source-Based**: GitHub Issue → `github-issue-handler`, GitHub PR → `github-pr-review`, Jira → `jira-code-plan`, Slack → `slack-inquiry`

**Task Type**: Discovery → `planning`, Implementation → `executor`, Verification → `verifier`, Integration → `service-integrator`

## Response Posting

**MUST**: After completing a task, agents MUST post responses back to source:

- GitHub: `github:add_issue_comment` (works for issues and PRs)
- Jira: `jira:add_jira_comment`
- Slack: `slack:post_message` (with `thread_ts` to reply in thread)

## Folder Structure

```
agent-engine/
├── main.py              # FastAPI app + task worker
├── cli/                 # CLI providers (claude.py, cursor.py)
├── config/              # Settings
├── .claude/             # Agents and skills
│   ├── agents/          # 13 agent definitions
│   └── skills/          # 9 skill definitions
└── tests/               # Co-located tests
    ├── factories/       # Task and session factories
    ├── conftest.py      # Shared fixtures
    └── test_*.py        # Test files
```

## Testing

Tests are co-located with the service for portability.

```bash
# From groote-ai root
make test-agent-engine

# Or directly
cd groote-ai
PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/ -v
```

### Test Factories

Import factories from `tests/factories/`:

```python
from .factories import TaskFactory, SessionFactory, TaskStatus
from .factories.task_factory import InvalidTransitionError, VALID_TRANSITIONS
```

## Environment Variables

- `CLI_PROVIDER`: `claude` or `cursor`
- `MAX_CONCURRENT_TASKS`: Maximum parallel tasks (default: 5)
- `TASK_TIMEOUT_SECONDS`: Task timeout limit (default: 3600)
- `REDIS_URL`: Redis connection string
- `DATABASE_URL`: PostgreSQL connection string
- `KNOWLEDGE_GRAPH_URL`: Knowledge graph service URL

## Development Rules

- Maximum 300 lines per file
- NO `any` types - use strict Pydantic models
- NO comments - self-explanatory code only
- Tests must run fast (< 5 seconds), no real network calls
- Use async/await for all I/O operations

## Agent Team Patterns

The Brain agent can create agent teams for complex tasks. When working as a teammate within the agent-engine:

### Available Team Strategies

1. **parallel_review**: Multiple reviewers analyze different aspects simultaneously
2. **decomposed_feature**: Planning → Implementation → Verification pipeline
3. **competing_hypotheses**: Multiple agents investigate different theories
4. **cross_layer**: Each agent owns a different module/service layer

### File Ownership Rules

- Each teammate is assigned specific files/directories
- NEVER edit files outside your assignment
- If you discover a needed change outside your scope, report it to the lead
- The lead resolves cross-cutting concerns after teammates complete
