"""G3 graph: required tools, bounded model-directed retrieval, checked assessment."""

from langgraph.graph import END, START, StateGraph

from .agent_nodes import AgentNodes
from .agent_state import AgentState


def create_agent_graph(context, ledger, knowledge, chat):
    nodes = AgentNodes(context, ledger, knowledge, chat)
    graph = StateGraph(AgentState)
    for name, node in [
        ("query_case", nodes.query),
        ("validate_materials", nodes.validate),
        ("retrieve_clauses", nodes.retrieve),
        ("model_decision", nodes.decide),
        ("supplement_retrieval", nodes.supplement),
        ("checked_assessment", nodes.assess),
    ]:
        graph.add_node(name, node)
    graph.add_edge(START, "query_case")
    graph.add_edge("query_case", "validate_materials")
    graph.add_edge("validate_materials", "retrieve_clauses")
    graph.add_edge("retrieve_clauses", "model_decision")
    graph.add_conditional_edges(
        "model_decision",
        lambda state: "supplement_retrieval" if state.get("pendingTool") else "checked_assessment",
    )
    graph.add_conditional_edges(
        "supplement_retrieval",
        lambda state: "checked_assessment" if state.get("stopReason") else "model_decision",
    )
    graph.add_edge("checked_assessment", END)
    return graph.compile()
