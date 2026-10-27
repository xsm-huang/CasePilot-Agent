"""V1 orchestration with official persistent approval checkpoints."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .workspace_nodes import WorkspaceNodes


class WorkspaceState(TypedDict, total=False):
    taskId: str
    analysis: dict
    review: dict


def create_workspace_graph(store, knowledge, chat_factory, checkpointer):
    nodes = WorkspaceNodes(store, knowledge, chat_factory)
    graph = StateGraph(WorkspaceState)
    for name, node in [
        ("analyze", nodes.analyze),
        ("human_review", nodes.human),
        ("summary", nodes.summary),
        ("findings", nodes.findings),
        ("recommendations", nodes.recommendations),
        ("complete", nodes.complete),
        ("reject", nodes.reject),
    ]:
        graph.add_node(name, node)
    graph.add_edge(START, "analyze")
    graph.add_conditional_edges(
        "analyze", lambda state: "human_review" if state["analysis"]["needsReview"] else "summary"
    )
    graph.add_conditional_edges(
        "human_review",
        lambda state: "reject" if state["review"]["decision"] == "reject" else "summary",
    )
    graph.add_edge("summary", "findings")
    graph.add_edge("findings", "recommendations")
    graph.add_edge("recommendations", "complete")
    graph.add_edge("complete", END)
    graph.add_edge("reject", END)
    return graph.compile(checkpointer=checkpointer)
