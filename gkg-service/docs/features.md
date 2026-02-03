# gkg-service - Features

Auto-generated on 2026-02-03

## Overview

GitLab Knowledge Graph service for code entity relationship analysis. Provides graph-based queries for understanding code structure, dependencies, and usage patterns.

## Features

### Dependency Analysis [TESTED]

Query file dependencies with configurable depth

**Related Tests:**
- `test_dependency_query_returns_file_dependencies`
- `test_dependency_query_respects_depth_parameter`

### Call Graph Analysis [TESTED]

Get function call graph with direction control (callers/callees/both)

**Related Tests:**
- `test_call_graph_returns_callers_and_callees`
- `test_call_graph_respects_direction_callers_only`
- `test_call_graph_respects_direction_callees_only`

### Class Hierarchy [TESTED]

Get class inheritance hierarchy (parents and children)

**Related Tests:**
- `test_hierarchy_returns_parents_and_children`

### Related Entities [TESTED]

Find related entities by relationship type

**Related Tests:**
- `test_related_entities_returns_relationships`

### Batch Operations [TESTED]

Query multiple entities in a single request

**Related Tests:**
- `test_batch_related_returns_results_for_all_entities`
- `test_batch_disabled_returns_empty`

### Caching [TESTED]

Cache query results for performance

**Related Tests:**
- `test_cached_dependencies_returned_on_repeat_query`

### Health Check [TESTED]

Service health check based on analyzer availability

**Related Tests:**
- `test_healthy_when_analyzer_available`
- `test_unhealthy_when_analyzer_unavailable`

### POST /analyze/dependencies [TESTED]

Get file dependencies

**Related Tests:**
- `test_dependency_query_returns_file_dependencies`
- `test_dependency_query_respects_depth_parameter`

### POST /query/usages [NEEDS TESTS]

Find symbol usages

### POST /graph/calls [TESTED]

Get function call graph

**Related Tests:**
- `test_call_graph_returns_callers_and_callees`

### POST /graph/hierarchy [TESTED]

Get class hierarchy

**Related Tests:**
- `test_hierarchy_returns_parents_and_children`

### POST /graph/related [TESTED]

Find related entities

**Related Tests:**
- `test_related_entities_returns_relationships`

### POST /index [NEEDS TESTS]

Index a repository

## Test Coverage Summary

| Metric | Count |
|--------|-------|
| Total Features | 14 |
| Fully Tested | 12 |
| Partially Tested | 0 |
| Missing Tests | 2 |
| **Coverage** | **85.7%** |
