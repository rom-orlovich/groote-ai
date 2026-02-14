# Documentation Templates

Templates derived from gold-standard services. Replace `{placeholders}` with actual values from source code.

For CLAUDE.md templates per service type, see `claude-templates.md`.

## ARCHITECTURE.md Template

Based on `api-gateway/docs/ARCHITECTURE.md`:

```markdown
# {Service Name} Architecture

## Overview

{1-2 sentence description of the service's role in the system.}

## Design Principles

1. **{Principle 1}** - {Description}
2. **{Principle 2}** - {Description}
3. **{Principle 3}** - {Description}

## Component Architecture

\`\`\`mermaid
graph TB
    subgraph External["{External Inputs}"]
        {Input nodes}
    end

    subgraph Service["{Service Name} :{port}"]
        {Internal components}
    end

    subgraph Storage["{Data Layer}"]
        {Storage nodes}
    end

    {Connections between nodes}
\`\`\`

## Directory Structure

\`\`\`
{service-dir}/
├── {file}    # {Purpose}
├── {dir}/    # {Purpose}
└── tests/    # Co-located tests
\`\`\`

## Data Flow

### {Primary Flow Name}

\`\`\`mermaid
sequenceDiagram
    participant {Actor1}
    participant {Actor2}
    {Sequence steps}
\`\`\`

## {Data Models / Key Structures}

{Model descriptions with JSON or code examples}

## Integration Points

### With {Service A}
\`\`\`
{Service} -> {Protocol} -> {Service A}
\`\`\`

## Testing Strategy

Tests focus on **behavior**, not implementation:
- {Test example 1}
- {Test example 2}
```

## features.md Template

Based on `api-gateway/docs/features.md`:

```markdown
# {Service Name} - Features

## Overview

{1-2 sentence service description.}

## Core Features

### {Feature 1 Name}

{2-3 sentence description of what this feature does.}

**Capabilities:**
- {Capability 1}
- {Capability 2}
- {Capability 3}

### {Feature 2 Name}

{2-3 sentence description.}

**{Relevant Detail Category}:**
- {Detail 1}
- {Detail 2}

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `{path}` | {METHOD} | {Description} |

## {MCP Tools / CLI Commands / UI Features}

| {Name} | Description |
|---------|-------------|
| `{tool/command}` | {Description} |
```

## flows.md Template

Based on `api-gateway/docs/flows.md`:

```markdown
# {Service Name} - Flows

## Process Flows

### {Flow 1 Name}

\`\`\`
[{Source}] -> {Action} -> [{Component}]
                                  |
                          [{Next Step}]
                                  |
                     [{Decision Point}]
                          |           |
                      [{Yes}]     [{No}]
                        |            |
                   [{Result}]   [{Result}]
\`\`\`

**Processing Steps:**
1. {Step 1}
2. {Step 2}
3. {Step 3}

### {Flow 2 Name}

\`\`\`
{ASCII flow diagram}
\`\`\`

**Processing Steps:**
1. {Step 1}
2. {Step 2}
```

## README Documentation Section

Every README must include this section (adapt links to service):

```markdown
## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams and data flows
- [Features](docs/features.md) - Feature list and capabilities
- [Flows](docs/flows.md) - Process flow documentation
```

## ASCII Flow Diagram Conventions

- Use `[Brackets]` for components/actors
- Use `->` or `-->` for connections
- Use `|` and `-` for vertical/horizontal lines
- Use indentation for nested flows
- Number processing steps below each diagram
- Keep diagrams under 40 characters wide when possible
