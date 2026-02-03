# llamaindex-service - Flows

Auto-generated on 2026-02-03

## Process Flows

### Hybrid Query Flow [TESTED]

**Steps:**
1. Receive POST request with query and source_types
2. Check cache for existing results
3. If cached, return cached results
4. Query vector store for each source type
5. If GKG enrichment enabled, enrich code results
6. Sort results by relevance score
7. Limit to top_k results
8. Cache results
9. Return response

**Related Tests:**
- `test_hybrid_query_returns_results_from_multiple_sources`
- `test_query_respects_top_k_limit`
- `test_results_sorted_by_relevance`
- `test_cached_results_returned_on_repeat_query`

### Code Query Flow [TESTED]

**Steps:**
1. Receive POST request with code query
2. Set source_types to ["code"] only
3. Apply repository filter if provided
4. Query code collection in vector store
5. Optionally enrich with graph context
6. Return code-specific results

**Related Tests:**
- `test_code_query_only_searches_code_collection`
- `test_code_query_applies_repository_filter`

### Graph Enrichment Flow [TESTED]

**Steps:**
1. Take code search results
2. For each code result, query GKG for relationships
3. Add callers/callees/dependencies to result
4. Return enriched results

**Related Tests:**
- `test_graph_enrichment_adds_context_to_code_results`
- `test_graph_enrichment_disabled_skips_graph_lookup`

### Related Entities Flow [TESTED]

**Steps:**
1. Receive POST request with entity info
2. Check if graph store is available
3. If not available, return empty map
4. Query graph store for relationships
5. Return relationship map

**Related Tests:**
- `test_get_related_entities_returns_relationships`
- `test_get_related_entities_without_graph_store_returns_empty`

### Caching Flow [TESTED]

**Steps:**
1. Generate cache key from query params
2. Check cache for key
3. If found and not expired, return cached
4. If not found, execute query
5. Store result in cache with TTL
6. Return result

**Related Tests:**
- `test_cached_results_returned_on_repeat_query`
- `test_caching_disabled_always_queries_store`

## Flow Coverage Summary

| Metric | Count |
|--------|-------|
| Total Flows | 5 |
| Fully Tested | 5 |
| Partially Tested | 0 |
| Missing Tests | 0 |
| **Coverage** | **100.0%** |
