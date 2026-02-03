# Agent Engine Architecture

## Overview

The Agent Engine is a scalable task execution engine with multi-CLI provider support. It consumes tasks from Redis queue, executes them using CLI providers (Claude/Cursor), orchestrates 13 specialized agents, and posts results back to sources.

## Design Principles

1. **Provider Agnostic** - Abstract CLI interface supports multiple providers
2. **Horizontal Scaling** - Multiple replicas consume from shared queue
3. **Agent Specialization** - 13 agents optimized for specific task types
4. **Real-Time Streaming** - Output streamed to Redis Pub/Sub and WebSocket

## Component Architecture

```mermaid
graph TB
    subgraph Queue["Task Queue"]
        RQ[(Redis Queue)]
    end

    subgraph Engine["Agent Engine :8080-8089"]
        TW[Task Worker]
        CF[CLI Factory]

        subgraph Providers["CLI Providers"]
            CL[Claude CLI]
            CU[Cursor CLI]
        end

        subgraph Agents["Agent System"]
            BR[Brain Agent]
            PL[Planning Agent]
            EX[Executor Agent]
            VR[Verifier Agent]
            GH[GitHub Handler]
            JR[Jira Handler]
            SL[Slack Handler]
        end
    end

    subgraph MCP["MCP Servers"]
        GM[GitHub MCP]
        JM[Jira MCP]
        SM[Slack MCP]
    end

    subgraph Output["Output Layer"]
        PS[Pub/Sub Stream]
        WS[WebSocket Hub]
        DB[(PostgreSQL)]
    end

    RQ --> TW
    TW --> CF
    CF --> CL
    CF --> CU

    CL --> Agents
    CU --> Agents

    Agents --> MCP

    TW --> PS
    TW --> WS
    TW --> DB
```

## Directory Structure

```
agent-engine/
├── main.py                    # FastAPI app + task worker
├── cli/
│   ├── base.py                # CLIProvider protocol
│   ├── factory.py             # Provider factory
│   ├── sanitization.py        # Output sanitization
│   └── providers/
│       ├── claude.py          # Claude CLI provider
│       └── cursor.py          # Cursor CLI provider
├── services/
│   └── knowledge.py           # Knowledge service integration
├── config/
│   └── settings.py            # Configuration
├── .claude/
│   ├── agents/                # 13 agent definitions
│   │   ├── brain.md
│   │   ├── planning.md
│   │   ├── executor.md
│   │   ├── verifier.md
│   │   ├── github-issue-handler.md
│   │   ├── github-pr-review.md
│   │   ├── jira-code-plan.md
│   │   ├── slack-inquiry.md
│   │   ├── service-integrator.md
│   │   ├── self-improvement.md
│   │   ├── agent-creator.md
│   │   ├── skill-creator.md
│   │   └── webhook-generator.md
│   ├── skills/                # 9 skill definitions
│   └── CLAUDE.md              # Agent orchestration config
├── mcp.json                   # MCP server connections
└── tests/
    ├── factories/             # Test data factories
    ├── conftest.py            # Shared fixtures
    └── test_*.py              # Test files
```

## CLI Provider Protocol

```mermaid
classDiagram
    class CLIProviderProtocol {
        <<interface>>
        +execute(prompt: str, model: str) AsyncIterator
        +is_available() bool
        +get_version() str
    }

    class ClaudeProvider {
        +execute(prompt, model)
        +is_available()
        +get_version()
    }

    class CursorProvider {
        +execute(prompt, model)
        +is_available()
        +get_version()
    }

    CLIProviderProtocol <|.. ClaudeProvider
    CLIProviderProtocol <|.. CursorProvider
```

## Data Flow

### Task Execution Flow

```mermaid
sequenceDiagram
    participant RQ as Redis Queue
    participant TW as Task Worker
    participant CF as CLI Factory
    participant CLI as CLI Provider
    participant MCP as MCP Servers
    participant DB as PostgreSQL
    participant PS as Pub/Sub

    TW->>RQ: BRPOP agent:tasks
    RQ-->>TW: Task
    TW->>DB: Status: in_progress
    TW->>CF: Get Provider
    CF-->>TW: Claude/Cursor CLI
    TW->>CLI: Execute with Agent Prompt

    loop Streaming Output
        CLI-->>TW: Output Chunk
        TW->>PS: Publish Output
    end

    CLI->>MCP: Tool Calls (via agent)
    MCP-->>CLI: Tool Results

    CLI-->>TW: Completion
    TW->>DB: Status: completed
    TW->>PS: Final Result
```

## Agent System

### Core Agents (Orchestration)

| Agent | Model | Purpose |
|-------|-------|---------|
| brain | opus | Central orchestrator, delegates to specialists |
| planning | opus | Discovery + PLAN.md creation |
| executor | sonnet | TDD implementation |
| verifier | opus | Quality verification |

### Workflow Agents (Source-Specific)

| Agent | Trigger | Purpose |
|-------|---------|---------|
| github-issue-handler | GitHub issues/comments | Handle GitHub issues |
| github-pr-review | Pull requests | Review PRs |
| jira-code-plan | Jira tickets | Plan Jira work |
| slack-inquiry | Slack mentions | Answer Slack questions |

### Support Agents

| Agent | Purpose |
|-------|---------|
| service-integrator | External service coordination |
| self-improvement | Memory + learning |
| agent-creator | Dynamic agent generation |
| skill-creator | Dynamic skill generation |
| webhook-generator | Webhook configuration |

## Task State Machine

```mermaid
stateDiagram-v2
    [*] --> pending: Task Created
    pending --> in_progress: Worker Picks Up
    in_progress --> completed: Success
    in_progress --> failed: Error
    in_progress --> awaiting_input: User Input Required
    awaiting_input --> in_progress: Input Received
    completed --> [*]
    failed --> [*]
```

## Scaling Model

```mermaid
graph TB
    subgraph Redis["Redis Queue"]
        Q[agent:tasks]
    end

    subgraph Replicas["Agent Engine Replicas"]
        R1[Replica 1 :8080]
        R2[Replica 2 :8081]
        R3[Replica 3 :8082]
    end

    Q --> R1
    Q --> R2
    Q --> R3
```

Each replica:
- Independently consumes from shared queue
- Has its own CLI process
- Logs health to PostgreSQL

## Testing Strategy

Tests focus on **behavior**, not implementation:

- ✅ "Task transitions from pending to in_progress"
- ✅ "Claude provider selected when CLI_PROVIDER=claude"
- ✅ "Output streamed to Pub/Sub"
- ❌ "subprocess.Popen called with correct arguments"

## Integration Points

### With API Gateway
```
API Gateway → LPUSH agent:tasks → Agent Engine
```

### With MCP Servers
```json
{
  "mcpServers": {
    "github": {"url": "http://github-mcp:9001/sse"},
    "jira": {"url": "http://jira-mcp:9002/sse"},
    "slack": {"url": "http://slack-mcp:9003/sse"},
    "sentry": {"url": "http://sentry-mcp:9004/sse"}
  }
}
```

### With API Services (Response Posting)
```
Agent Engine → github-api → GitHub
Agent Engine → jira-api → Jira
Agent Engine → slack-api → Slack
```
