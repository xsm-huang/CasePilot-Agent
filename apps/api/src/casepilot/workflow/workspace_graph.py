"""Closed-claim orchestration with persistent approval checkpoints."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .workspace_nodes import WorkspaceNodes


class WorkspaceState(TypedDict, total=False):
    taskId: str
    analysis: dict


def create_workspace_graph(store, knowledge, chat_factory, checkpointer):
    nodes = WorkspaceNodes(store, knowledge, chat_factory)
    graph = StateGraph(WorkspaceState)
    graph.add_node("analyze", nodes.analyze)
    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", END)
    return graph.compile(checkpointer=checkpointer)
