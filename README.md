# langgraph-checkpoint-neo4j

Neo4j implementation of LangGraph checkpoint saver for persistent agent memory.

## Installation

```bash
pip install langgraph-checkpoint-neo4j
```

## Usage

### Synchronous

```python
from neo4j import GraphDatabase
from langgraph.checkpoint.neo4j import Neo4jSaver

# Create driver
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

# Create checkpointer
checkpointer = Neo4jSaver(driver)
checkpointer.setup()  # Create indexes/constraints

# Use with LangGraph
from langgraph.graph import StateGraph

graph = StateGraph(...)
compiled = graph.compile(checkpointer=checkpointer)

# Run with thread_id for persistence
config = {"configurable": {"thread_id": "my-thread"}}
result = compiled.invoke({"messages": [...]}, config)
```

### Asynchronous

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
```

### Context Manager

```python
from langgraph.checkpoint.neo4j import Neo4jSaver

with Neo4jSaver.from_conn_string("bolt://localhost:7687", "neo4j", "password") as checkpointer:
    checkpointer.setup()
    # Use checkpointer...
```

## Neo4j Schema

The checkpointer creates the following node types:

- `Checkpoint` - Main checkpoint storage
- `CheckpointBlob` - Large channel value storage
- `CheckpointWrite` - Pending write storage

## Development

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=langgraph.checkpoint.neo4j
```

## License

MIT
