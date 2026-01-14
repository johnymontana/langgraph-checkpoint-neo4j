# langgraph-checkpoint-neo4j

Neo4j implementation of LangGraph checkpoint saver for persistent agent memory with branching time-travel support.

## Features

- **Persistent Agent Memory**: Store and retrieve LangGraph checkpoints in Neo4j
- **Graph-Native Data Model**: Leverages Neo4j relationships for efficient traversal
- **Branching Time-Travel**: Fork conversations from any checkpoint without losing history
- **Sync and Async Support**: Both synchronous and asynchronous implementations
- **Human-Readable Storage**: Checkpoint data stored as JSON for easy debugging
- **Demo Application**: Full-stack demo with FastAPI backend and Next.js frontend

## Architecture

```
langgraph-checkpoint-neo4j/
├── langgraph/checkpoint/neo4j/    # Main package
│   ├── __init__.py                # Neo4jSaver (sync)
│   ├── aio.py                     # AsyncNeo4jSaver (async)
│   ├── base.py                    # BaseNeo4jSaver, Cypher queries
│   ├── _internal.py               # Sync connection utilities
│   └── _ainternal.py              # Async connection utilities
├── tests/                         # Test suite
│   ├── conftest.py                # Pytest fixtures with testcontainers
│   ├── test_sync.py               # Sync checkpointer tests
│   └── test_async.py              # Async checkpointer tests
└── demo/                          # Demo application
    ├── backend/                   # FastAPI + LangGraph agent
    └── frontend/                  # Next.js + Chakra UI v3
```

## Neo4j Graph Data Model

The checkpointer uses a proper graph model with nodes and relationships:

```
                         ┌─────────────────────────────────────┐
                         │                                     │
                         ▼                                     │
(:Thread)──[HAS_CHECKPOINT]──►(:Checkpoint)──[PREVIOUS]────────┘
    │                              │
    │                    ┌─────────┼─────────┐
    │                    │         │         │
    ▼                    ▼         ▼         ▼
[HAS_BRANCH]       [HAS_CHANNEL] [HAS_WRITE] [ON_BRANCH]
    │                    │         │         │
    ▼                    ▼         ▼         │
(:Branch)◄────────(:ChannelState) (:PendingWrite)
    │                                        │
    └────────────[HEAD]──────────────────────┘
```

### Node Types

| Node | Description | Key Properties |
|------|-------------|----------------|
| `Thread` | Conversation thread | `thread_id`, `checkpoint_ns` |
| `Checkpoint` | Point-in-time state | `checkpoint_id`, `checkpoint`, `metadata`, `created_at` |
| `ChannelState` | Channel value storage | `channel`, `version`, `type`, `blob` |
| `PendingWrite` | Fault-tolerant writes | `task_id`, `channel`, `blob`, `idx` |
| `Branch` | Conversation branch | `branch_id`, `name`, `fork_point_id`, `created_at` |

### Relationships

| Relationship | Description |
|--------------|-------------|
| `HAS_CHECKPOINT` | Thread owns checkpoints |
| `PREVIOUS` | Checkpoint parent chain |
| `HAS_CHANNEL` | Checkpoint to channel states |
| `HAS_WRITE` | Checkpoint to pending writes |
| `HAS_BRANCH` | Thread owns branches |
| `ACTIVE_BRANCH` | Thread's current active branch |
| `HEAD` | Branch's latest checkpoint |
| `ON_BRANCH` | Checkpoint belongs to branch |

![Demo app graph view](img/graph_view.png)

## Installation

```bash
pip install langgraph-checkpoint-neo4j
```

Or with uv:

```bash
uv add langgraph-checkpoint-neo4j
```

## Quick Start

### Synchronous Usage

```python
from neo4j import GraphDatabase
from langgraph.checkpoint.neo4j import Neo4jSaver
from langgraph.graph import StateGraph

# Create Neo4j driver
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

# Create and setup checkpointer
checkpointer = Neo4jSaver(driver)
checkpointer.setup()  # Creates indexes and constraints

# Build your LangGraph agent
graph = StateGraph(...)
compiled = graph.compile(checkpointer=checkpointer)

# Run with thread_id for persistence
config = {"configurable": {"thread_id": "my-conversation"}}
result = compiled.invoke({"messages": [("user", "Hello!")]}, config)

# Continue the conversation (state is automatically restored)
result = compiled.invoke({"messages": [("user", "What did I just say?")]}, config)
```

### Asynchronous Usage

```python
from neo4j import AsyncGraphDatabase
from langgraph.checkpoint.neo4j.aio import AsyncNeo4jSaver

# Create async driver
driver = AsyncGraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

# Create async checkpointer
checkpointer = AsyncNeo4jSaver(driver)
await checkpointer.setup()

# Use with async LangGraph
compiled = graph.compile(checkpointer=checkpointer)
result = await compiled.ainvoke({"messages": [...]}, config)

# Don't forget to close
await checkpointer.close()
```

### Context Manager (Recommended)

```python
from langgraph.checkpoint.neo4j import Neo4jSaver

with Neo4jSaver.from_conn_string(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
) as checkpointer:
    checkpointer.setup()
    graph = builder.compile(checkpointer=checkpointer)
    result = graph.invoke({"messages": [...]}, config)
```

### Async Context Manager

```python
from langgraph.checkpoint.neo4j.aio import AsyncNeo4jSaver

async with await AsyncNeo4jSaver.from_conn_string(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
) as checkpointer:
    await checkpointer.setup()
    graph = builder.compile(checkpointer=checkpointer)
    result = await graph.ainvoke({"messages": [...]}, config)
```

## Branching Time-Travel

The checkpointer supports non-destructive time-travel through branching. When you "restore" to a previous checkpoint, a new branch is created instead of deleting history.

### How It Works

1. **Main Branch**: Created automatically on first checkpoint
2. **Active Branch**: Each thread has one active branch
3. **HEAD**: Points to the latest checkpoint on the active branch
4. **Forking**: Creates a new branch from any historical checkpoint

### Using Branches Directly

```python
from langgraph.checkpoint.neo4j.base import (
    CYPHER_CREATE_BRANCH,
    CYPHER_SET_ACTIVE_BRANCH,
    CYPHER_LIST_BRANCHES,
)

# List branches for a thread
with driver.session() as session:
    result = session.run(
        CYPHER_LIST_BRANCHES,
        {"thread_id": "my-thread", "checkpoint_ns": ""}
    )
    for branch in result:
        print(f"Branch: {branch['name']}, Active: {branch['is_active']}")

# Create a new branch from a checkpoint
with driver.session() as session:
    session.run(
        CYPHER_CREATE_BRANCH,
        {
            "thread_id": "my-thread",
            "checkpoint_ns": "",
            "branch_id": "my-fork",
            "name": "experiment-1",
            "fork_point_id": "checkpoint-id-to-fork-from"
        }
    )

# Switch active branch
with driver.session() as session:
    session.run(
        CYPHER_SET_ACTIVE_BRANCH,
        {
            "thread_id": "my-thread",
            "checkpoint_ns": "",
            "branch_id": "my-fork"
        }
    )
```

## Demo Application

The repository includes a full-stack demo application showcasing all features.

![Demo app chat view](img/chat_view.png)

### Running the Demo

```bash
cd demo
docker-compose up -d
```

This starts:
- **Neo4j**: http://localhost:7474 (browser) / bolt://localhost:7687
- **Backend**: http://localhost:8000 (FastAPI)
- **Frontend**: http://localhost:3000 (Next.js)

### Demo Features

- Create and manage conversation threads
- Chat with an AI agent (uses OpenAI gpt-4o-mini)
- View checkpoint history timeline
- Fork from any checkpoint (time-travel)
- Switch between branches
- Tools: Calculator and Weather lookup

### Environment Variables

Create a `.env` file in `demo/`:

```env
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
OPENAI_API_KEY=your-openai-api-key
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### Backend API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/threads` | List all threads |
| POST | `/api/threads` | Create new thread |
| DELETE | `/api/threads/{id}` | Delete thread |
| GET | `/api/messages/{threadId}` | Get thread messages |
| POST | `/api/messages/{threadId}` | Send message |
| GET | `/api/history/{threadId}/checkpoints` | List checkpoints |
| GET | `/api/history/{threadId}/branches` | List branches |
| POST | `/api/history/{threadId}/fork` | Fork from checkpoint |
| POST | `/api/history/{threadId}/switch-branch` | Switch active branch |
| POST | `/api/history/{threadId}/time-travel` | Fork and switch (time-travel) |
| GET | `/api/history/{threadId}/tree` | Get checkpoint tree |

## Development

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (for running tests with testcontainers)

### Setup

```bash
# Clone the repository
git clone https://github.com/johnymontana/langgraph-checkpoint-neo4j.git
cd langgraph-checkpoint-neo4j

# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=langgraph.checkpoint.neo4j

# Run specific test file
uv run pytest tests/test_sync.py -v

# Run branch-related tests only
uv run pytest tests/test_sync.py -k "branch" -v
```

### Project Structure

```
langgraph-checkpoint-neo4j/
├── pyproject.toml              # Package configuration
├── uv.lock                     # Dependency lock file
├── .python-version             # Python version (3.10)
├── langgraph/
│   └── checkpoint/
│       └── neo4j/
│           ├── __init__.py     # Neo4jSaver class
│           ├── aio.py          # AsyncNeo4jSaver class
│           ├── base.py         # Base class, Cypher queries
│           ├── _internal.py    # Sync utilities
│           ├── _ainternal.py   # Async utilities
│           └── py.typed        # PEP 561 marker
├── tests/
│   ├── conftest.py             # Test fixtures
│   ├── test_sync.py            # 23 sync tests
│   └── test_async.py           # Async tests
└── demo/
    ├── docker-compose.yml
    ├── backend/
    │   ├── pyproject.toml
    │   └── app/
    │       ├── main.py         # FastAPI app
    │       ├── routers/
    │       │   ├── threads.py
    │       │   ├── messages.py
    │       │   └── history.py  # Branch/time-travel endpoints
    │       └── agent/
    │           ├── graph.py    # LangGraph agent
    │           └── tools.py    # Calculator, Weather tools
    └── frontend/
        ├── package.json
        ├── app/                # Next.js pages
        ├── components/
        │   ├── ChatInterface.tsx
        │   ├── MessageList.tsx
        │   ├── ThreadList.tsx
        │   └── HistoryTimeline.tsx  # Branch UI
        └── lib/
            ├── api.ts          # API client
            └── types.ts        # TypeScript types
```

### Running Tests

Tests use [testcontainers](https://testcontainers.com/) to spin up a real Neo4j instance:

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test class
uv run pytest tests/test_sync.py::TestNeo4jSaver -v

# Run with coverage report
uv run pytest --cov=langgraph.checkpoint.neo4j --cov-report=html
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy langgraph/
```

## Cypher Query Reference

### Viewing the Graph in Neo4j Browser

```cypher
// View threads and their checkpoints
MATCH (t:Thread)-[r1:HAS_CHECKPOINT]->(c:Checkpoint)
OPTIONAL MATCH (c)-[r2:PREVIOUS]->(parent:Checkpoint)
OPTIONAL MATCH (c)-[r3:HAS_CHANNEL]->(cs:ChannelState)
RETURN t, c, parent, cs, r1, r2, r3 LIMIT 50

// View branches for a thread
MATCH (t:Thread {thread_id: "your-thread-id"})-[:HAS_BRANCH]->(b:Branch)
OPTIONAL MATCH (t)-[:ACTIVE_BRANCH]->(active:Branch)
OPTIONAL MATCH (b)-[:HEAD]->(head:Checkpoint)
RETURN b.name, b.branch_id, 
       active.branch_id = b.branch_id as is_active,
       head.checkpoint_id

// Trace checkpoint chain (history)
MATCH path = (c:Checkpoint)-[:PREVIOUS*]->(root:Checkpoint)
WHERE NOT (root)-[:PREVIOUS]->()
RETURN path

// Count entities
MATCH (t:Thread) RETURN 'Threads' as type, count(t) as count
UNION ALL
MATCH (c:Checkpoint) RETURN 'Checkpoints' as type, count(c) as count
UNION ALL
MATCH (b:Branch) RETURN 'Branches' as type, count(b) as count
```

## Configuration

### Neo4jSaver Options

| Parameter | Type | Description |
|-----------|------|-------------|
| `driver` | `Driver` | Neo4j driver instance |
| `database` | `str \| None` | Database name (default: Neo4j default) |

### Connection String Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `uri` | `str` | Neo4j connection URI |
| `user` | `str` | Neo4j username |
| `password` | `str` | Neo4j password |
| `database` | `str \| None` | Database name |

## Requirements

- Python >= 3.10
- Neo4j >= 5.0
- langgraph-checkpoint >= 2.0.0
- neo4j (Python driver) >= 5.0.0

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`uv run pytest`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request
