"""Pytest fixtures for Neo4j checkpoint saver tests."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
import pytest_asyncio
from neo4j import AsyncGraphDatabase, GraphDatabase

from langgraph.checkpoint.neo4j import Neo4jSaver
from langgraph.checkpoint.neo4j.aio import AsyncNeo4jSaver

# Check if we should use testcontainers or an existing Neo4j instance
USE_TESTCONTAINERS = os.environ.get("USE_TESTCONTAINERS", "true").lower() == "true"
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")


@pytest.fixture(scope="session")
def neo4j_container() -> Generator[dict[str, str], None, None]:
    """Start Neo4j container for testing or use existing instance.

    Returns connection parameters as a dictionary.
    """
    if USE_TESTCONTAINERS:
        try:
            from testcontainers.neo4j import Neo4jContainer

            container = Neo4jContainer("neo4j:5.15-community")
            container.start()

            yield {
                "uri": container.get_connection_url(),
                "user": container.username,
                "password": container.password,
            }

            container.stop()
        except ImportError:
            pytest.skip("testcontainers not installed, skipping container tests")
    else:
        # Use existing Neo4j instance
        yield {
            "uri": NEO4J_URI,
            "user": NEO4J_USER,
            "password": NEO4J_PASSWORD,
        }


@pytest.fixture
def neo4j_driver(neo4j_container: dict[str, str]) -> Generator:
    """Create a Neo4j driver for testing."""
    driver = GraphDatabase.driver(
        neo4j_container["uri"],
        auth=(neo4j_container["user"], neo4j_container["password"]),
    )
    yield driver
    driver.close()


@pytest.fixture
def neo4j_saver(neo4j_driver) -> Generator[Neo4jSaver, None, None]:
    """Create a Neo4jSaver for testing."""
    saver = Neo4jSaver(neo4j_driver)
    saver.setup()
    yield saver


@pytest.fixture
def clean_neo4j_saver(neo4j_saver: Neo4jSaver) -> Generator[Neo4jSaver, None, None]:
    """Create a Neo4jSaver and clean up test data after each test."""
    yield neo4j_saver
    # Clean up after test - delete all test data
    with neo4j_saver._driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")


@pytest_asyncio.fixture
async def async_neo4j_driver(neo4j_container: dict[str, str]):
    """Create an async Neo4j driver for testing."""
    driver = AsyncGraphDatabase.driver(
        neo4j_container["uri"],
        auth=(neo4j_container["user"], neo4j_container["password"]),
    )
    yield driver
    await driver.close()


@pytest_asyncio.fixture
async def async_neo4j_saver(async_neo4j_driver) -> AsyncNeo4jSaver:
    """Create an AsyncNeo4jSaver for testing."""
    saver = AsyncNeo4jSaver(async_neo4j_driver)
    await saver.setup()
    return saver


@pytest_asyncio.fixture
async def clean_async_neo4j_saver(async_neo4j_saver: AsyncNeo4jSaver) -> AsyncNeo4jSaver:
    """Create an AsyncNeo4jSaver and clean up test data after each test."""
    yield async_neo4j_saver
    # Clean up after test - delete all test data
    async with async_neo4j_saver._driver.session() as session:
        await session.run("MATCH (n) DETACH DELETE n")


@pytest.fixture
def sample_checkpoint() -> dict:
    """Create a sample checkpoint for testing."""
    return {
        "v": 1,
        "id": "checkpoint-1",
        "ts": "2024-01-01T00:00:00Z",
        "channel_values": {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        },
        "channel_versions": {
            "messages": "00000000000000000001.0000000000000000",
        },
        "versions_seen": {},
        "pending_sends": [],
    }


@pytest.fixture
def sample_metadata() -> dict:
    """Create sample checkpoint metadata for testing."""
    return {
        "source": "input",
        "step": 0,
        "writes": {},
        "parents": {},
    }


@pytest.fixture
def sample_config() -> dict:
    """Create a sample config for testing."""
    return {
        "configurable": {
            "thread_id": "test-thread-1",
            "checkpoint_ns": "",
        }
    }
