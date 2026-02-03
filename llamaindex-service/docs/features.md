# llamaindex-service - Features

Auto-generated on 2026-02-03

## Overview

Hybrid RAG orchestration service combining vector search (ChromaDB) with graph traversal (GKG). Provides multi-source semantic search across code, Jira tickets, and Confluence docs.

## Features

### Hybrid Query [TESTED]

Query across multiple source types with combined results

**Related Tests:**
- `test_hybrid_query_returns_results_from_multiple_sources`
- `test_query_respects_top_k_limit`
- `test_results_sorted_by_relevance`

### Code-Specific Search [TESTED]

Search code with repository filtering

**Related Tests:**
- `test_code_query_only_searches_code_collection`
- `test_code_query_applies_repository_filter`

### Graph Enrichment [TESTED]

Enrich results with code relationship context from GKG

**Related Tests:**
- `test_graph_enrichment_adds_context_to_code_results`
- `test_graph_enrichment_disabled_skips_graph_lookup`

### Query Caching [TESTED]

Cache query results with configurable TTL

**Related Tests:**
- `test_cached_results_returned_on_repeat_query`
- `test_caching_disabled_always_queries_store`

### Related Entities [TESTED]

Find related code entities via graph

**Related Tests:**
- `test_get_related_entities_returns_relationships`
- `test_get_related_entities_without_graph_store_returns_empty`

### POST /query [TESTED]

Hybrid query across all sources

**Related Tests:**
- `test_hybrid_query_returns_results_from_multiple_sources`

### POST /query/code [TESTED]

Code-specific search

**Related Tests:**
- `test_code_query_only_searches_code_collection`

### POST /query/tickets [NEEDS TESTS]

Jira ticket search

### POST /query/docs [NEEDS TESTS]

Confluence search

### POST /graph/related [TESTED]

Find related entities via graph

**Related Tests:**
- `test_get_related_entities_returns_relationships`

### GET /collections [NEEDS TESTS]

List ChromaDB collections

### GET /health [NEEDS TESTS]

Health check endpoint

## Test Coverage Summary

| Metric | Count |
|--------|-------|
| Total Features | 13 |
| Fully Tested | 9 |
| Partially Tested | 0 |
| Missing Tests | 4 |
| **Coverage** | **69.2%** |
