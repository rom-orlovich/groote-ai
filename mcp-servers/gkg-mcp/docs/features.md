# GKG MCP - Features

## Overview

FastMCP-based MCP server that exposes 5 code analysis tools powered by the GKG (GitLab Knowledge Graph) service. Provides dependency analysis, symbol tracking, call graphs, and class hierarchies.

## Core Features

### Dependency Analysis

Analyze import and dependency relationships of files and modules with configurable traversal depth.

**Capabilities:**
- Analyze dependencies of a specific file path
- Configurable traversal depth (default: 3 levels)
- Organization and repository scoping
- Returns formatted dependency tree

### Symbol Usage Tracking

Find all usages of a symbol (function, class, variable) across the codebase.

**Capabilities:**
- Search by symbol name across all indexed repositories
- Repository filtering with glob patterns
- Results include file paths, line numbers, and usage context

### Call Graph Analysis

Get function call relationships showing both callers and callees.

**Capabilities:**
- Analyze callers (who calls this function)
- Analyze callees (what this function calls)
- Bidirectional analysis (both callers and callees)
- Configurable traversal depth

### Class Hierarchy

Get inheritance hierarchy for classes showing parent and child classes.

**Capabilities:**
- Discover parent classes and interfaces
- Find subclasses and implementations
- Repository filtering

### Entity Relationships

Find entities related to a specific code entity through various relationship types.

**Capabilities:**
- Query by entity name and type (function, class, module, file)
- Filter by relationship type (calls, imports, extends, references, all)
- Results grouped by relationship type with file locations

## MCP Tools

| Tool | Description |
|------|-------------|
| `analyze_dependencies` | Analyze file/module dependencies with depth control |
| `find_usages` | Find all usages of a symbol across repositories |
| `get_call_graph` | Get function callers and callees graph |
| `get_class_hierarchy` | Get class inheritance hierarchy |
| `get_related_entities` | Find related entities by relationship type |
