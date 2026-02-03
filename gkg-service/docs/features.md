# GKG Service - Features

## Overview

GitLab Knowledge Graph service for code entity relationship analysis. Provides graph-based queries for understanding code structure, dependencies, and usage patterns.

## Core Features

### Dependency Analysis

Query file dependencies with configurable depth for understanding code relationships.

**Capabilities:**
- Direct dependencies (imports, requires)
- Transitive dependencies with depth control
- Dependency direction (imports vs imported-by)
- Cross-file relationship mapping

### Call Graph Analysis

Build function/method call graphs for control flow understanding.

**Analysis Types:**
- Callers (who calls this function)
- Callees (what does this function call)
- Call depth traversal
- Cross-module calls

### Symbol Usage Search

Find all usages of symbols (classes, functions, variables) across codebase.

**Search Capabilities:**
- Definition location
- All reference locations
- Usage context (assignment, call, import)
- Usage filtering by scope

### Class Hierarchy

Analyze inheritance and interface relationships.

**Hierarchy Features:**
- Parent classes
- Child classes (implementations)
- Interface implementations
- Trait/mixin usage

### Related Entities

Find entities related by various relationship types.

**Relationship Types:**
- Imports/exports
- Function calls
- Type references
- Variable assignments

### Repository Indexing

Index repositories to build the knowledge graph.

**Indexing Features:**
- Full repository indexing
- Incremental updates
- Multi-language support
- Git history awareness

### Result Caching

Cache query results for performance.

**Cache Features:**
- Query result caching
- Configurable TTL
- Cache invalidation on index update

## API Endpoints

### Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze/dependencies` | POST | Get file dependencies |
| `/query/usages` | POST | Find symbol usages |
| `/graph/calls` | POST | Get function call graph |
| `/graph/hierarchy` | POST | Get class hierarchy |
| `/graph/related` | POST | Find related entities |

### Indexing

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/index` | POST | Index repository |
| `/index/status` | GET | Indexing status |

### Health

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
