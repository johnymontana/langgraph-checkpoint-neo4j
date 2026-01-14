"""LangGraph agent definition with tool calling."""

from __future__ import annotations

from collections.abc import Sequence
from operator import add
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from langgraph.checkpoint.neo4j.aio import AsyncNeo4jSaver

from ..config import settings
from .tools import TOOLS


class AgentState(TypedDict):
    """State for the agent graph."""

    messages: Annotated[Sequence[BaseMessage], add]


def should_continue(state: AgentState) -> str:
    """Determine if we should continue to tools or end."""
    messages = state["messages"]
    last_message = messages[-1]

    # If the last message has tool calls, route to tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Otherwise, end
    return END


async def call_model(state: AgentState) -> AgentState:
    """Call the LLM with the current messages."""
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.7,
    ).bind_tools(TOOLS)

    response = await llm.ainvoke(state["messages"])
    return {"messages": [response]}


def create_agent_graph(checkpointer: AsyncNeo4jSaver):
    """Create and compile the agent graph.

    Args:
        checkpointer: The Neo4j checkpoint saver for persistence.

    Returns:
        A compiled LangGraph StateGraph.
    """
    # Create the graph
    builder = StateGraph(AgentState)

    # Add nodes
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode(TOOLS))

    # Set entry point
    builder.set_entry_point("agent")

    # Add conditional edges
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )

    # Tools always go back to agent
    builder.add_edge("tools", "agent")

    # Compile with checkpointer
    return builder.compile(checkpointer=checkpointer)
