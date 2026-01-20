"""FastAPI application for the LangGraph Neo4j checkpointer demo."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_neo4j import AsyncNeo4jSaver
from neo4j import AsyncGraphDatabase

from .config import settings
from .models import HealthResponse
from .routers import history, messages, threads


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup: Initialize Neo4j connection and checkpointer
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    checkpointer = AsyncNeo4jSaver(driver)
    await checkpointer.setup()

    app.state.driver = driver
    app.state.checkpointer = checkpointer

    yield

    # Shutdown: Close connections
    await driver.close()


app = FastAPI(
    title="LangGraph Chat API",
    description="Demo API for Neo4j-backed LangGraph agent with memory persistence",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(threads.router, prefix="/api/threads", tags=["threads"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(history.router, prefix="/api/history", tags=["history"])


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """Check the health of the service."""
    neo4j_connected = False

    try:
        # Try to verify Neo4j connectivity
        driver = app.state.driver
        await driver.verify_connectivity()
        neo4j_connected = True
    except Exception:
        pass

    return HealthResponse(
        status="healthy" if neo4j_connected else "degraded",
        neo4j_connected=neo4j_connected,
    )


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "LangGraph Chat API",
        "version": "1.0.0",
        "description": "Neo4j-backed LangGraph agent with memory persistence",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
    }
