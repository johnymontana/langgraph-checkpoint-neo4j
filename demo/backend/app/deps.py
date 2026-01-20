"""Dependency injection for FastAPI."""

from __future__ import annotations

from fastapi import Request
from langchain_neo4j import AsyncNeo4jSaver


async def get_checkpointer(request: Request) -> AsyncNeo4jSaver:
    """Get the checkpointer from app state."""
    return request.app.state.checkpointer


async def get_driver(request: Request):
    """Get the Neo4j driver from app state."""
    return request.app.state.driver
