# Docs-Tests Sync Templates

## Architecture Document Template

```markdown
# {service_name} Architecture

## Overview

{purpose_from_readme}

## Design Principles

1. **Protocol-Based Interfaces** - All external dependencies implement typed protocols
2. **Dependency Injection** - Components wired via factory at startup
3. **Behavior-Focused Testing** - Tests verify business behavior, not implementation

## Component Architecture

```mermaid
graph TB
    subgraph Clients["Internal Clients"]
        {client_components}
    end

    subgraph Service["{service_name} :port"]
        {service_components}
    end

    subgraph External["External Services"]
        {external_services}
    end

    Clients --> Service
    Service --> External
```

## Directory Structure

```
{service_path}/
├── main.py                    # Application entry point
├── api/                       # HTTP layer
│   └── routes.py              # Route handlers
├── core/                      # Business logic
│   ├── interfaces.py          # Protocol definitions
│   └── models.py              # Domain models
├── adapters/                  # External implementations
├── config/                    # Configuration
└── tests/                     # Behavior-driven tests
```

## Data Flow

{data_flow_description}

```mermaid
sequenceDiagram
    {sequence_diagram}
```

## Protocol Interfaces

{protocol_definitions}
```

---

## Features Document Template

```markdown
# {service_name} - Features

## Overview

{overview_from_readme}

## Core Features

### {feature_name}

{feature_description}

**Capabilities:**
- {capability_1}
- {capability_2}
- {capability_3}

**Configuration:**
- {config_option}: {description}

## API Endpoints

### {endpoint_category}

| Endpoint | Method | Description |
|----------|--------|-------------|
| `{path}` | {method} | {description} |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| {VAR_NAME} | {default} | {description} |
```

---

## Flows Document Template

```markdown
# {service_name} - Flows

## Process Flows

### {flow_name}

```
[Input] → [Step 1] → [Step 2]
              ↓
         [Decision]
            ↓       ↓
         [Yes]    [No]
            ↓       ↓
         [Action] [Action]
```

**Processing Steps:**
1. {step_1_description}
2. {step_2_description}
3. {step_3_description}

**Configuration:**
- {config_param}: {description}
```

---

## Sync Report Template

```markdown
# Documentation Sync Report

Generated: {datetime}

## Summary

| Metric | Value |
|--------|-------|
| Services | {service_count} |
| Features Documented | {feature_count} |
| Flows Documented | {flow_count} |

## Service Reports

### {service_name}

- **Features:** {count}
- **Flows:** {count}
- **API Endpoints:** {count}

**Generated Docs:**
- {service}/docs/ARCHITECTURE.md
- {service}/docs/features.md
- {service}/docs/flows.md

---
```

---

## Service Documentation Entry Template

```markdown
## {service_name}

### Overview
{brief_description}

### Core Features
- {feature_1}
- {feature_2}
- {feature_3}

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| {path} | {method} | {description} |

### Process Flows
- {flow_1}: {brief_description}
- {flow_2}: {brief_description}

**Generated Docs:**
- {service}/docs/ARCHITECTURE.md
- {service}/docs/features.md
- {service}/docs/flows.md
```

---

## Console Output Template

```
Discovered {count} services

Processing: {service_name}
  - Extracted {feature_count} features
  - Identified {flow_count} flows
  - Documented {endpoint_count} endpoints
  - Generated: ARCHITECTURE.md
  - Generated: features.md
  - Generated: flows.md

============================================================
SYNC COMPLETE
============================================================
  [OK] {service_name}: {feature_count} features, {flow_count} flows
  [OK] {service_name}: {feature_count} features, {flow_count} flows

Total: {service_count} services documented
```

---

## ASCII Flow Diagram Conventions

Use these symbols for flow diagrams:

```
→ ← ↑ ↓       # Arrows for flow direction
│ ─           # Lines for connections
┌ ┐ └ ┘       # Corners
├ ┤ ┬ ┴ ┼    # Junctions
▼ ▲           # Direction indicators

[Box]         # Process step
{Decision}    # Decision point (use ↓ branches)
(Input)       # External input/output
```

Example flow:
```
[Client] → POST /endpoint → [Parse Request]
                                  ↓
                          [Process Data]
                                  ↓
                          [Decision?]
                             ↓       ↓
                          [Yes]    [No]
                             ↓       ↓
                          [A]      [B]
                             │       │
                             └───────┘
                                  ↓
                          [Return Response]
```
