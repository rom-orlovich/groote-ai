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

## Node Types

Repository, File, Function, Class, Module, Variable, Constant, Import, Agent, Skill, Task

## Node Model

```rust
pub struct Node {
    pub id: Uuid,
    pub name: String,
    pub node_type: NodeType,
    pub path: Option<String>,
    pub language: Option<String>,
    pub description: Option<String>,
    pub metadata: serde_json::Value,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}
```

## Edge Types

Contains, Imports, Calls, Inherits, Implements, Uses, DependsOn, DefinedIn, References, Handles, Delegates

## Edge Model

```rust
pub struct Edge {
    pub id: Uuid,
    pub source_id: Uuid,
    pub target_id: Uuid,
    pub edge_type: EdgeType,
    pub weight: f64,
    pub metadata: serde_json::Value,
    pub created_at: DateTime<Utc>,
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
- **serde** / **serde_json** - Serialization
- **petgraph** - Graph data structures and algorithms
- **uuid** - Node and edge identifiers
- **chrono** - Timestamps
- **tower-http** - CORS and tracing middleware

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams and data flows
- [Features](docs/features.md) - Feature list and capabilities
- [Flows](docs/flows.md) - Process flow documentation
