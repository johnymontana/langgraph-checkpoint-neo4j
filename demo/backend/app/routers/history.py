"""History and time-travel endpoints with branch support."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from langgraph.checkpoint.neo4j.aio import AsyncNeo4jSaver
from langgraph.checkpoint.neo4j.base import (
    CYPHER_CREATE_BRANCH,
    CYPHER_GET_CHECKPOINT_TREE,
    CYPHER_LIST_BRANCHES,
    CYPHER_SET_ACTIVE_BRANCH,
    CYPHER_UPDATE_BRANCH_HEAD,
)

from ..deps import get_checkpointer
from ..models import (
    Branch,
    CheckpointDetail,
    CheckpointSummary,
    CheckpointTree,
    CheckpointTreeNode,
    ForkRequest,
    SwitchBranchRequest,
    TimeTravelRequest,
)
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


@router.get("/{thread_id}/branches", response_model=list[Branch])
async def list_branches(
    thread_id: str,
    checkpointer: AsyncNeo4jSaver = Depends(get_checkpointer),
) -> list[Branch]:
    """List all branches for a thread."""
    async with checkpointer._driver.session() as session:
        result = await session.run(
            CYPHER_LIST_BRANCHES,
            {"thread_id": thread_id, "checkpoint_ns": ""},
        )
        branches = []
        async for record in result:
            created_at = record["created_at"]
            # Convert Neo4j datetime to Python datetime if needed
            if hasattr(created_at, "to_native"):
                created_at = created_at.to_native()
            branches.append(
                Branch(
                    branch_id=record["branch_id"],
                    name=record["name"],
                    created_at=created_at,
                    fork_point_id=record["fork_point_id"],
                    is_active=record["is_active"],
                    head_checkpoint_id=record["head_checkpoint_id"],
                )
            )
        return branches


@router.post("/{thread_id}/fork", response_model=Branch)
async def fork_branch(
    thread_id: str,
    request: ForkRequest,
    checkpointer: AsyncNeo4jSaver = Depends(get_checkpointer),
) -> Branch:
    """Create a new branch from a checkpoint."""
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

    # Generate branch name if not provided
    branch_id = str(uuid.uuid4())
    branch_name = request.name or f"fork-{branch_id[:8]}"

    async with checkpointer._driver.session() as session:
        # Create the new branch
        await session.run(
            CYPHER_CREATE_BRANCH,
            {
                "thread_id": thread_id,
                "checkpoint_ns": "",
                "branch_id": branch_id,
                "name": branch_name,
                "fork_point_id": request.checkpoint_id,
            },
        )

    return Branch(
        branch_id=branch_id,
        name=branch_name,
        created_at=datetime.utcnow(),
        fork_point_id=request.checkpoint_id,
        is_active=False,
        head_checkpoint_id=request.checkpoint_id,
    )


@router.post("/{thread_id}/switch-branch")
async def switch_branch(
    thread_id: str,
    request: SwitchBranchRequest,
    checkpointer: AsyncNeo4jSaver = Depends(get_checkpointer),
) -> dict:
    """Switch the active branch for a thread."""
    async with checkpointer._driver.session() as session:
        result = await session.run(
            CYPHER_SET_ACTIVE_BRANCH,
            {
                "thread_id": thread_id,
                "checkpoint_ns": "",
                "branch_id": request.branch_id,
            },
        )
        record = await result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Branch not found")

    # Get the HEAD checkpoint messages for the new active branch
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
    tuple_ = await checkpointer.aget_tuple(config)

    messages = []
    if tuple_:
        raw_messages = tuple_.checkpoint.get("channel_values", {}).get("messages", [])
        messages = [convert_message(msg) for msg in raw_messages]

    return {
        "status": "switched",
        "thread_id": thread_id,
        "branch_id": request.branch_id,
        "messages": [m.model_dump() for m in messages],
    }


@router.get("/{thread_id}/tree", response_model=CheckpointTree)
async def get_checkpoint_tree(
    thread_id: str,
    checkpointer: AsyncNeo4jSaver = Depends(get_checkpointer),
) -> CheckpointTree:
    """Get the full checkpoint tree for visualization."""
    async with checkpointer._driver.session() as session:
        # Get all checkpoints with their relationships
        result = await session.run(
            CYPHER_GET_CHECKPOINT_TREE,
            {"thread_id": thread_id, "checkpoint_ns": ""},
        )
        nodes = []
        async for record in result:
            nodes.append(
                CheckpointTreeNode(
                    checkpoint_id=record["checkpoint_id"],
                    parent_id=record["parent_id"],
                    branch_id=record["branch_id"],
                    branch_name=record["branch_name"],
                )
            )

        # Get all branches
        branch_result = await session.run(
            CYPHER_LIST_BRANCHES,
            {"thread_id": thread_id, "checkpoint_ns": ""},
        )
        branches = []
        async for record in branch_result:
            created_at = record["created_at"]
            if hasattr(created_at, "to_native"):
                created_at = created_at.to_native()
            branches.append(
                Branch(
                    branch_id=record["branch_id"],
                    name=record["name"],
                    created_at=created_at,
                    fork_point_id=record["fork_point_id"],
                    is_active=record["is_active"],
                    head_checkpoint_id=record["head_checkpoint_id"],
                )
            )

    return CheckpointTree(nodes=nodes, branches=branches)


@router.post("/{thread_id}/time-travel")
async def time_travel(
    thread_id: str,
    request: TimeTravelRequest,
    checkpointer: AsyncNeo4jSaver = Depends(get_checkpointer),
) -> dict:
    """Time travel to a specific checkpoint by forking (non-destructive).

    This creates a new branch from the specified checkpoint and switches to it,
    preserving all existing checkpoints.
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

    # Generate branch name
    branch_id = str(uuid.uuid4())
    branch_name = request.branch_name or f"fork-{branch_id[:8]}"

    async with checkpointer._driver.session() as session:
        # Create the new branch from the checkpoint
        await session.run(
            CYPHER_CREATE_BRANCH,
            {
                "thread_id": thread_id,
                "checkpoint_ns": "",
                "branch_id": branch_id,
                "name": branch_name,
                "fork_point_id": request.checkpoint_id,
            },
        )

        # Switch to the new branch
        await session.run(
            CYPHER_SET_ACTIVE_BRANCH,
            {
                "thread_id": thread_id,
                "checkpoint_ns": "",
                "branch_id": branch_id,
            },
        )

        # Update branch HEAD to the fork point checkpoint
        await session.run(
            CYPHER_UPDATE_BRANCH_HEAD,
            {
                "thread_id": thread_id,
                "checkpoint_ns": "",
                "checkpoint_id": request.checkpoint_id,
            },
        )

    # Get messages from the checkpoint
    raw_messages = tuple_.checkpoint.get("channel_values", {}).get("messages", [])
    messages = [convert_message(msg) for msg in raw_messages]

    return {
        "status": "forked",
        "thread_id": thread_id,
        "checkpoint_id": request.checkpoint_id,
        "branch_id": branch_id,
        "branch_name": branch_name,
        "messages": [m.model_dump() for m in messages],
    }
