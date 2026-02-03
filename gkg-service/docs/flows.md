# gkg-service - Flows

Auto-generated on 2026-02-03

## Process Flows

### Dependency Query Flow [TESTED]

**Steps:**
1. Receive POST request with file_path and depth
2. Check cache for existing result
3. If cached, return cached result
4. Query graph analyzer for dependencies
5. Build dependency tree up to specified depth
6. Cache result
7. Return dependency tree

**Related Tests:**
- `test_dependency_query_returns_file_dependencies`
- `test_dependency_query_respects_depth_parameter`
- `test_cached_dependencies_returned_on_repeat_query`

### Call Graph Flow [TESTED]

**Steps:**
1. Receive POST request with function_name and direction
2. Query graph analyzer for call relationships
3. If direction is "callers", return only callers
4. If direction is "callees", return only callees
5. If direction is "both", return both
6. Return call graph

**Related Tests:**
- `test_call_graph_returns_callers_and_callees`
- `test_call_graph_respects_direction_callers_only`
- `test_call_graph_respects_direction_callees_only`

### Class Hierarchy Flow [TESTED]

**Steps:**
1. Receive POST request with class_name
2. Query graph analyzer for inheritance
3. Find parent classes
4. Find child classes
5. Return hierarchy tree

**Related Tests:**
- `test_hierarchy_returns_parents_and_children`

### Batch Query Flow [TESTED]

**Steps:**
1. Receive POST request with entity list
2. Check if batch operations enabled
3. If disabled, return empty results
4. Query each entity in parallel
5. Aggregate results
6. Return results map

**Related Tests:**
- `test_batch_related_returns_results_for_all_entities`
- `test_batch_disabled_returns_empty`

### Repository Indexing Flow [NEEDS TESTS]

**Steps:**
1. Receive POST request with repo_url
2. Clone repository to REPOS_DIR
3. Run GKG binary to index code
4. Store graph in DATA_DIR
5. Return indexing status

## Flow Coverage Summary

| Metric | Count |
|--------|-------|
| Total Flows | 5 |
| Fully Tested | 4 |
| Partially Tested | 0 |
| Missing Tests | 1 |
| **Coverage** | **80.0%** |
