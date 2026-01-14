"""Pydantic models for the demo API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ThreadCreate(BaseModel):
    """Request model for creating a new thread."""

    name: str | None = None


class Thread(BaseModel):
    """Response model for a conversation thread."""

    id: str
    name: str
    created_at: datetime
    last_message_at: datetime | None = None
    message_count: int = 0


class MessageCreate(BaseModel):
    """Request model for sending a message."""

    content: str = Field(..., min_length=1)


class Message(BaseModel):
    """Response model for a chat message."""

    role: str  # "user" | "assistant" | "tool"
    content: str
    timestamp: datetime
    tool_calls: list[dict] | None = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    messages: list[Message]
    thread_id: str


class CheckpointSummary(BaseModel):
    """Summary of a checkpoint for listing."""

    checkpoint_id: str
    step: int
    source: str  # "input" | "loop" | "update"
    timestamp: datetime
    message_count: int


class CheckpointDetail(BaseModel):
    """Detailed checkpoint information."""

    checkpoint_id: str
    step: int
    source: str
    timestamp: datetime
    messages: list[Message]
    parent_checkpoint_id: str | None = None


class TimeTravelRequest(BaseModel):
    """Request model for time travel (now forks instead of deleting)."""

    checkpoint_id: str
    branch_name: str | None = None  # Optional name for the new branch


class Branch(BaseModel):
    """Response model for a branch."""

    branch_id: str
    name: str
    created_at: datetime
    fork_point_id: str | None = None
    is_active: bool = False
    head_checkpoint_id: str | None = None


class ForkRequest(BaseModel):
    """Request model for forking a branch."""

    checkpoint_id: str
    name: str | None = None  # Optional name for the new branch


class SwitchBranchRequest(BaseModel):
    """Request model for switching branches."""

    branch_id: str


class CheckpointTreeNode(BaseModel):
    """A node in the checkpoint tree."""

    checkpoint_id: str
    parent_id: str | None = None
    branch_id: str | None = None
    branch_name: str | None = None


class CheckpointTree(BaseModel):
    """Full checkpoint tree for visualization."""

    nodes: list[CheckpointTreeNode]
    branches: list[Branch]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    neo4j_connected: bool
