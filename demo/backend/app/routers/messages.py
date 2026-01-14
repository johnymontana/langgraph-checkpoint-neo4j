"""Message and chat endpoints."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from langgraph.checkpoint.neo4j.aio import AsyncNeo4jSaver

from ..agent.graph import create_agent_graph
from ..deps import get_checkpointer
from ..models import ChatResponse, Message, MessageCreate

router = APIRouter()


def convert_message(msg) -> Message:
    """Convert a LangChain message to our Message model."""
    role = "assistant"
    tool_calls = None

    if isinstance(msg, HumanMessage):
        role = "user"
    elif isinstance(msg, AIMessage):
        role = "assistant"
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_calls = msg.tool_calls
    elif isinstance(msg, ToolMessage):
        role = "tool"
    elif hasattr(msg, "type"):
        role = msg.type

    content = msg.content if hasattr(msg, "content") else str(msg)

    return Message(
        role=role,
        content=content,
        timestamp=datetime.utcnow(),
        tool_calls=tool_calls,
    )


@router.get("/{thread_id}", response_model=list[Message])
async def get_messages(
    thread_id: str,
    checkpointer: AsyncNeo4jSaver = Depends(get_checkpointer),
) -> list[Message]:
    """Get all messages for a thread."""
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}

    tuple_ = await checkpointer.aget_tuple(config)

    if not tuple_:
        return []

    # Extract messages from checkpoint
    messages = tuple_.checkpoint.get("channel_values", {}).get("messages", [])

    return [convert_message(msg) for msg in messages]


@router.post("/{thread_id}", response_model=ChatResponse)
async def send_message(
    thread_id: str,
    message: MessageCreate,
    checkpointer: AsyncNeo4jSaver = Depends(get_checkpointer),
) -> ChatResponse:
    """Send a message and get AI response."""
    graph = create_agent_graph(checkpointer)

    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}

    # Create human message
    human_msg = HumanMessage(content=message.content)

    # Run the graph
    result = await graph.ainvoke(
        {"messages": [human_msg]},
        config,
    )

    # Convert messages to our model
    messages = [convert_message(msg) for msg in result["messages"]]

    return ChatResponse(messages=messages, thread_id=thread_id)


@router.post("/{thread_id}/stream")
async def stream_message(
    thread_id: str,
    message: MessageCreate,
    checkpointer: AsyncNeo4jSaver = Depends(get_checkpointer),
):
    """Stream AI response with server-sent events."""
    graph = create_agent_graph(checkpointer)
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}

    human_msg = HumanMessage(content=message.content)

    async def generate():
        async for event in graph.astream(
            {"messages": [human_msg]},
            config,
            stream_mode="values",
        ):
            # Convert messages in event
            if "messages" in event:
                messages = [
                    {
                        "role": convert_message(msg).role,
                        "content": convert_message(msg).content,
                    }
                    for msg in event["messages"]
                ]
                yield f"data: {json.dumps({'messages': messages})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
