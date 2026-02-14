# Knowledge Graph - Features

## Overview

In-memory graph database for code entity relationships. Stores nodes (functions, classes, files) and edges (calls, imports, inherits) with typed relationships, weighted path finding, and text-based search.

## Core Features

### Node Management

Store and retrieve code entities as typed graph nodes. Each node has a UUID, name, type, optional file path, language, description, and arbitrary JSON metadata.

**Node Types:**
- Repository, File, Function, Class, Module
- Variable, Constant, Import
- Agent, Skill, Task

**Operations:**
- List all nodes with count
- Create node with auto-generated UUID and timestamps
- Get node by ID with edge count
- Delete node (cascades to connected edges)

### Edge Management

Store typed, weighted relationships between nodes. Edges connect source and target nodes with a relationship type, weight (default 1.0), and optional metadata.

**Edge Types:**
- Contains, Imports, Calls, Inherits, Implements
- Uses, DependsOn, DefinedIn, References
- Handles, Delegates

**Operations:**
- List all edges with source/target node names
- Create edge (validates both nodes exist)

### Path Finding

Find shortest paths between any two nodes using Dijkstra's algorithm with edge weights. Returns the full path as UUIDs, resolved node names, and total weight.

**Capabilities:**
- Weighted shortest path via Dijkstra
- Path reconstruction with node name resolution
- Total weight calculation

### Neighbor Discovery

Traverse the graph from a starting node to find related entities. Supports directional traversal (incoming, outgoing, both), edge type filtering, and configurable depth.

**Parameters:**
- `node_id` - Starting node
- `direction` - incoming, outgoing, or both (default: both)
- `edge_types` - Optional filter by relationship type
- `depth` - Traversal depth (default: 1)

### Text Search

Search nodes by name or description substring matching. Supports filtering by node type and programming language with configurable result limits.

**Parameters:**
- `query` - Text substring to match against name and description
- `node_types` - Optional filter by node type
- `language` - Optional filter by programming language
- `limit` - Maximum results (default: 20)

### Graph Statistics

Retrieve aggregate metrics about the graph including total counts, type distributions, and density metrics.

**Metrics:**
- Total node and edge counts
- Nodes grouped by type
- Edges grouped by type
- Average edges per node

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/nodes` | GET | List all nodes |
| `/api/v1/nodes` | POST | Create node |
| `/api/v1/nodes/{id}` | GET | Get node by ID |
| `/api/v1/nodes/{id}` | DELETE | Delete node |
| `/api/v1/edges` | GET | List all edges |
| `/api/v1/edges` | POST | Create edge |
| `/api/v1/query/path` | POST | Find shortest path |
| `/api/v1/query/neighbors` | POST | Find neighbors |
| `/api/v1/query/search` | POST | Search nodes |
| `/api/v1/stats` | GET | Graph statistics |
