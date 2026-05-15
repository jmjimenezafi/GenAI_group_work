from langgraph.graph import END, StateGraph

from utils.agents.workflow_models import WorkflowState
from utils.rag.rag_agent import rag_agent 
from utils.rag.rag_report_generator import rag_report_agent
from utils.agents.A_websearch_agent.search_agent import search_agent
from utils.agents.B_facts_agent.facts_agent import facts_agent
from utils.agents.C_source_classifier.source_class_agent import source_class_agent
from utils.agents.D_report_agent.report_agent import report_agent


def _rag_route(state: WorkflowState) -> str:
    can_answer = bool(state.rag_response and state.rag_response.can_answer)
    return "rag_report" if can_answer else "search"

def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("rag", rag_agent)
    graph.add_node("search", search_agent)
    graph.add_node("facts", facts_agent)
    graph.add_node("source_classification", source_class_agent)
    graph.add_node("report", report_agent)
    graph.add_node("rag_report", rag_report_agent)


    graph.set_entry_point("rag")
    graph.add_conditional_edges(
        "rag",
        _rag_route,
        {
            "rag_report": "rag_report",
            "search": "search",
        }
    )

    graph.add_edge("search", "facts")
    graph.add_edge("facts", "source_classification")
    graph.add_edge("source_classification", "report")
    graph.add_edge("report", END)
    graph.add_edge("rag_report", END)
    return graph.compile()

def run(query: str) -> WorkflowState:
    graph = build_workflow()
    result = graph.invoke(WorkflowState(query=query))
    if isinstance(result, WorkflowState):
        return result
    validator = getattr(WorkflowState, "model_validate", None)
    if validator:
        return validator(result)
    return WorkflowState.parse_obj(result)


