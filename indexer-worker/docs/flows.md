# Indexer Worker - Flows

## Process Flows

### Job Processing Flow

```
[Redis Queue] ← BRPOP indexer:jobs → [Indexer Worker]
                                           ↓
                                  [Update Status: running]
                                           ↓
                                  [Fetch Source Configs]
                                           ↓
                          ┌────────────────┼────────────────┐
                          │                │                │
                          ▼                ▼                ▼
                      [GitHub]         [Jira]        [Confluence]
                          │                │                │
                          ▼                ▼                ▼
                      [Index]          [Index]         [Index]
                          │                │                │
                          └────────────────┼────────────────┘
                                           ↓
                                  [Update Status: completed]
                                           ↓
                                  [Publish Completion Event]
```

**Processing Steps:**
1. Worker polls Redis queue for indexing jobs
2. Update job status to "running" in database
3. Fetch source configurations from Dashboard API
4. For each enabled source, create appropriate indexer
5. Index source to vector store (ChromaDB)
6. If GKG enabled, index code to graph store
7. Update job status to "completed"
8. Publish completion event to Redis Pub/Sub

### GitHub Indexing Flow

```
[GitHub Source Config] → [Clone/Pull Repository]
                               ↓
                      [Scan for Code Files]
                               ↓
                      [Filter by language/pattern]
                               ↓
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
         [Python]           [JS/TS]         [Other]
              │                │                │
              └────────────────┼────────────────┘
                               ↓
                      [Parse Source Files]
                               ↓
                      [Extract Entities]
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        [Functions]       [Classes]       [Imports]
              │                │                │
              └────────────────┼────────────────┘
                               ↓
                      [Chunk File Content]
                               ↓
                      [Generate Embeddings]
                               ↓
                      [Store in ChromaDB]
                               ↓
            [GKG Enabled?] ─────┼─────────────
                   ↓            │            ↓
                [Yes]           │          [No]
                   ↓            │            │
            [Index to GKG]      │            │
                   │            │            │
                   └────────────┘            │
                               ↓             │
                      [Return Success]←──────┘
```

**GitHub Indexing Details:**
- Clone via GITHUB_TOKEN authentication
- Incremental updates via git pull
- File filtering by extension (.py, .js, .ts, .go, etc.)
- AST parsing for entity extraction

### Jira Indexing Flow

```
[Jira Source Config] → [Authenticate with API]
                              ↓
                      [Fetch Projects]
                              ↓
                      [For each Project:]
                              ↓
                      [Fetch Issues (JQL)]
                              ↓
                      [For each Issue:]
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
         [Summary]      [Description]    [Comments]
              │               │               │
              └───────────────┼───────────────┘
                              ↓
                      [Chunk Content]
                              ↓
                      [Generate Embeddings]
                              ↓
                      [Store in ChromaDB]
```

**Jira Indexed Fields:**
- `summary` - Issue title
- `description` - Full description
- `comments` - All comments
- `labels`, `priority`, `status` - Metadata

### Chunking Flow

```
[Source Content] → [Detect Content Type]
                          ↓
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
           [Code]      [Text]      [HTML]
              │           │           │
              ▼           ▼           ▼
         [AST-aware]  [Sentence]  [Strip+Text]
              │           │           │
              └───────────┼───────────┘
                          ↓
                  [Split into chunks]
                          ↓
                  [Apply overlap]
                          ↓
                  [Return chunks]
```

**Chunking Parameters:**
```
CHUNK_SIZE=1500        # Characters per chunk
CHUNK_OVERLAP=200      # Overlap between chunks
```

### Embedding Generation Flow

```
[Content Chunks] → [Batch by size (32)]
                          ↓
                  [Load Embedding Model]
                          ↓
                  [For each batch:]
                          ↓
                  [Generate embeddings]
                          ↓
                  [Yield (chunk, embedding)]
```

**Embedding Configuration:**
- Model: sentence-transformers/all-MiniLM-L6-v2
- Batch size: 32
- GPU acceleration if available

### Vector Store Flow

```
[Chunks + Embeddings] → [Get/Create Collection]
                               ↓
                       [Prepare documents]
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
           [ids]         [embeddings]     [metadata]
              │                │                │
              └────────────────┼────────────────┘
                               ↓
                       [ChromaDB.add()]
                               ↓
                       [Return count]
```

**Collection Naming:**
- `code` - Code files
- `tickets` - Jira tickets
- `docs` - Confluence pages

### Parallel Processing Flow

```
[Multiple Repos] → [Check ENABLE_PARALLEL]
                          ↓
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
          [True]                  [False]
              │                       │
              ▼                       ▼
      [Create Thread Pool]     [Sequential]
              │                       │
              ▼                       │
      [Submit Repo Tasks]             │
              │                       │
              ▼                       │
      [Limit: MAX_PARALLEL_REPOS]     │
              │                       │
              ▼                       │
      [Collect Results]               │
              │                       │
              └───────────────────────┘
                          ↓
                  [Return Summary]
```

**Parallel Configuration:**
- Max parallel: 5 (configurable)
- Semaphore-based limiting
- Async/await for I/O operations
