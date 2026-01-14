"""History and time-travel endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from langgraph.checkpoint.neo4j.aio import AsyncNeo4jSaver

from ..deps import get_checkpointer
from ..models import CheckpointDetail, CheckpointSummary, TimeTravelRequest
from .messages import convert_message

router = APIRouter()


@router.get("/{thread_id}/checkpoints", response_model=list[CheckpointSummary])
async def list_checkpoints(
    thread_id: str,
    checkpointer: AsyncNeo4jSaver = Depends(get_checkpointer),
) -> list[CheckpointSummary]:
    """List all checkpoints for a thread (for time travel)."""
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}

    checkpoints = []
    async for tuple_ in checkpointer.alist(config):
        # Get message count from checkpoint
        messages = tuple_.checkpoint.get("channel_values", {}).get("messages", [])

        checkpoints.append(
            CheckpointSummary(
                checkpoint_id=tuple_.config["configurable"]["checkpoint_id"],
                step=tuple_.metadata.get("step", 0),
                source=tuple_.metadata.get("source", "unknown"),
                timestamp=datetime.utcnow(),  # Would come from checkpoint created_at
                message_count=len(messages),
            )
        )

    return checkpoints


@router.get("/{thread_id}/checkpoints/{checkpoint_id}", response_model=CheckpointDetail)
async def get_checkpoint(
    thread_id: str,
    checkpoint_id: str,
    checkpointer: AsyncNeo4jSaver = Depends(get_checkpointer),
) -> CheckpointDetail:
    """Get detailed checkpoint state for time travel view."""
    config = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_ns": "",
            "checkpoint_id": checkpoint_id,
        }
    }

    tuple_ = await checkpointer.aget_tuple(config)

    if not tuple_:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    # Get messages from checkpoint
    raw_messages = tuple_.checkpoint.get("channel_values", {}).get("messages", [])
    messages = [convert_message(msg) for msg in raw_messages]

    parent_id = None
    if tuple_.parent_config:
        parent_id = tuple_.parent_config["configurable"].get("checkpoint_id")

    return CheckpointDetail(
        checkpoint_id=checkpoint_id,
        step=tuple_.metadata.get("step", 0),
        source=tuple_.metadata.get("source", "unknown"),
        timestamp=datetime.utcnow(),
        messages=messages,
        parent_checkpoint_id=parent_id,
    )


@router.post("/{thread_id}/time-travel")
async def time_travel(
    thread_id: str,
    request: TimeTravelRequest,
    checkpointer: AsyncNeo4jSaver = Depends(get_checkpointer),
) -> dict:
    """Resume conversation from a specific checkpoint (fork).

    This returns configuration for the client to use in subsequent requests.
    The next message will create a new checkpoint branching from the specified point.
    """
    # Verify the checkpoint exists
    config = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_ns": "",
            "checkpoint_id": request.checkpoint_id,
        }
    }

    tuple_ = await checkpointer.aget_tuple(config)

    if not tuple_:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    return {
        "status": "ready",
        "thread_id": thread_id,
        "checkpoint_id": request.checkpoint_id,
        "message": "Conversation state restored. Send a message to continue from this point.",
        "config": config,
    }
