"""Graph topology only. Persisted node and branch names are unchanged."""

from langgraph.graph import END, START, StateGraph

from .nodes import AnalysisNodes
from .state import State


def create_graph(store, checkpointer):
    nodes = AnalysisNodes(store)
    graph = StateGraph(State)
    for name, node in [
        ("query_case", nodes.query),
        ("validate_materials", nodes.validate),
        ("retrieve_clauses", nodes.retrieve),
        ("human_review", nodes.human),
        ("generate_report", nodes.report),
    ]:
        graph.add_node(name, node)
    graph.add_edge(START, "query_case")
    graph.add_edge("query_case", "validate_materials")
    graph.add_edge("validate_materials", "retrieve_clauses")
    graph.add_conditional_edges(
        "retrieve_clauses", lambda state: "human_review" if state["findings"] else "generate_report"
    )
    graph.add_edge("human_review", "generate_report")
    graph.add_edge("generate_report", END)
    return graph.compile(checkpointer=checkpointer)
