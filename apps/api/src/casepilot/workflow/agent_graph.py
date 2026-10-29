"""G3 graph: required tools, bounded model-directed retrieval, checked assessment."""

from langgraph.graph import END, START, StateGraph

from .agent_nodes import AgentNodes
from .agent_state import AgentState


def create_agent_graph(context, ledger, knowledge, chat):
    nodes = AgentNodes(context, ledger, knowledge, chat)
    graph = StateGraph(AgentState)
    for name, node in [
        ("query_case", nodes.stage("archive", nodes.query)),
        ("archive", nodes.stage("archive", nodes.archive, finish=True)),
        ("coverage", nodes.stage("coverage", nodes.coverage, finish=True)),
        ("consistency", nodes.stage("consistency", nodes.consistency)),
        ("amount", nodes.stage("amount", nodes.amount, finish=True)),
        ("amount_rules", nodes.stage("amount", nodes.amount_rules)),
        ("validate_materials", nodes.stage("consistency", nodes.validate)),
        ("material_assessment", nodes.stage("consistency", nodes.material_assessment, finish=True)),
        ("retrieve_clauses", nodes.stage("clauses", nodes.retrieve)),
        ("model_decision", nodes.stage("clauses", nodes.decide)),
        ("supplement_retrieval", nodes.stage("clauses", nodes.supplement)),
        ("checked_assessment", nodes.stage("clauses", nodes.assess, finish=True)),
        ("finish", nodes.finish),
    ]:
        graph.add_node(name, node)
    graph.add_edge(START, "query_case")
    graph.add_edge("query_case", "archive")
    graph.add_edge("archive", "coverage")
    graph.add_edge("coverage", "consistency")
    graph.add_edge("consistency", "validate_materials")
    graph.add_edge("validate_materials", "amount_rules")
    graph.add_edge("amount_rules", "material_assessment")
    graph.add_edge("material_assessment", "retrieve_clauses")
    graph.add_edge("retrieve_clauses", "model_decision")
    graph.add_conditional_edges(
        "model_decision",
        lambda state: "supplement_retrieval" if state.get("pendingTool") else "checked_assessment",
    )
    graph.add_conditional_edges(
        "supplement_retrieval",
        lambda state: "checked_assessment" if state.get("stopReason") else "model_decision",
    )
    graph.add_edge("checked_assessment", "amount")
    graph.add_edge("amount", "finish")
    graph.add_edge("finish", END)
    return graph.compile()
