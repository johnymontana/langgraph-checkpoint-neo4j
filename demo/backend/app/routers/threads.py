"""Thread management endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from langgraph.checkpoint.neo4j.aio import AsyncNeo4jSaver

from ..deps import get_checkpointer
from ..models import Thread, ThreadCreate

router = APIRouter()


@router.get("/", response_model=list[Thread])
async def list_threads(
    checkpointer: AsyncNeo4jSaver = Depends(get_checkpointer),
) -> list[Thread]:
    """List all conversation threads."""
    threads = []

    # Query Neo4j for distinct thread_ids using the new graph model
    async with checkpointer._driver.session() as session:
        result = await session.run("""
            MATCH (t:Thread)-[:HAS_CHECKPOINT]->(c:Checkpoint)
            WITH t.thread_id as thread_id,
                 max(c.created_at) as last_activity,
                 min(c.created_at) as created_at,
                 count(c) as checkpoint_count
            RETURN thread_id, created_at, last_activity, checkpoint_count
            ORDER BY last_activity DESC
        """)

        async for record in result:
            thread_id = record["thread_id"]
            created_at = record["created_at"]
            last_activity = record["last_activity"]

            # Convert Neo4j datetime to Python datetime if needed
            if hasattr(created_at, "to_native"):
                created_at = created_at.to_native()
            if hasattr(last_activity, "to_native"):
                last_activity = last_activity.to_native()

            threads.append(
                Thread(
                    id=thread_id,
                    name=f"Thread {thread_id[:8]}...",
                    created_at=created_at or datetime.utcnow(),
                    last_message_at=last_activity,
                    message_count=record["checkpoint_count"],
                )
            )

    return threads


@router.post("/", response_model=Thread)
async def create_thread(
    thread: ThreadCreate | None = None,
) -> Thread:
    """Create a new conversation thread."""
    thread_id = str(uuid.uuid4())
    now = datetime.utcnow()
    name = thread.name if thread and thread.name else f"Thread {thread_id[:8]}..."

    return Thread(
        id=thread_id,
        name=name,
        created_at=now,
        last_message_at=None,
        message_count=0,
    )


@router.get("/{thread_id}", response_model=Thread)
async def get_thread(
    thread_id: str,
    checkpointer: AsyncNeo4jSaver = Depends(get_checkpointer),
) -> Thread:
    """Get a specific thread by ID."""
    async with checkpointer._driver.session() as session:
        result = await session.run(
            """
            MATCH (t:Thread {thread_id: $thread_id})-[:HAS_CHECKPOINT]->(c:Checkpoint)
            WITH t.thread_id as thread_id,
                 max(c.created_at) as last_activity,
                 min(c.created_at) as created_at,
                 count(c) as checkpoint_count
            RETURN thread_id, created_at, last_activity, checkpoint_count
        """,
            {"thread_id": thread_id},
        )

        record = await result.single()

        # For new threads without checkpoints, return a default thread
        if not record:
            return Thread(
                id=thread_id,
                name=f"Thread {thread_id[:8]}...",
                created_at=datetime.utcnow(),
                last_message_at=None,
                message_count=0,
            )

        created_at = record["created_at"]
        last_activity = record["last_activity"]

        if hasattr(created_at, "to_native"):
            created_at = created_at.to_native()
        if hasattr(last_activity, "to_native"):
            last_activity = last_activity.to_native()

        return Thread(
            id=thread_id,
            name=f"Thread {thread_id[:8]}...",
            created_at=created_at or datetime.utcnow(),
            last_message_at=last_activity,
            message_count=record["checkpoint_count"],
        )


@router.delete("/{thread_id}")
async def delete_thread(
    thread_id: str,
    checkpointer: AsyncNeo4jSaver = Depends(get_checkpointer),
) -> dict:
    """Delete a thread and all its checkpoints."""
    await checkpointer.adelete_thread(thread_id)
    return {"status": "deleted", "thread_id": thread_id}
