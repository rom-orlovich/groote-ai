# Knowledge Graph Service

Rust-based knowledge graph service for code entity relationships and semantic search. Provides a high-performance graph database for storing and querying code entities, enabling semantic code search, dependency tracking, and call graph analysis.

## Development

- Port: 4000
- Language: Rust
- Max 300 lines per file, no comments, strict types, async/await for I/O
- Tests: `cargo test`

## Architecture

The service follows a modular architecture built with Axum web framework and petgraph for graph operations.

## Directory Structure

- `src/main.rs` - Application entry point
- `src/api/` - HTTP handlers and routes
- `src/models/` - Node, Edge, and Query models
- `src/services/` - Graph service logic
- `config/repos.json` - Repository configuration

## Key Commands

```bash
# Build
cargo build --release

# Run locally
cargo run

# Run tests
cargo test

# Format
cargo fmt

# Lint
cargo clippy
```

## Node Model

Code entities are represented as nodes:

```rust
pub struct Node {
    pub id: String,
    pub node_type: NodeType,  // Function, Class, Module, File
    pub name: String,
    pub file_path: String,
    pub metadata: HashMap<String, String>,
}
```

## Edge Model

Relationships between entities:

```rust
pub struct Edge {
    pub id: String,
    pub source: String,        // Source node ID
    pub target: String,        // Target node ID
    pub edge_type: EdgeType,   // Calls, Imports, Inherits, References
    pub metadata: HashMap<String, String>,
}
```

## API Endpoints

### Nodes
- `GET /api/v1/nodes` - List all nodes
- `POST /api/v1/nodes` - Create node
- `GET /api/v1/nodes/{id}` - Get node by ID
- `DELETE /api/v1/nodes/{id}` - Delete node

### Edges
- `GET /api/v1/edges` - List all edges
- `POST /api/v1/edges` - Create edge

### Queries
- `POST /api/v1/query/path` - Find path between nodes
- `POST /api/v1/query/neighbors` - Find neighbors of a node
- `POST /api/v1/query/search` - Search nodes

### Statistics
- `GET /api/v1/stats` - Graph statistics

## Environment Variables

```bash
PORT=4000
RUST_LOG=debug
REPOS_CONFIG_PATH=/app/config/repos.json
```

## Health Check

```bash
curl http://localhost:4000/health
```

## Dependencies

- **axum** - Web framework
- **tokio** - Async runtime
- **serde** - Serialization
- **petgraph** - Graph data structures
- **sqlx** - Database access (PostgreSQL)
