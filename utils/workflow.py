from langgraph.graph import END, StateGraph

from utils.agents.workflow_models import WorkflowState
from utils.agents.A_websearch_agent.search_agent import search_agent
from utils.agents.B_facts_agent.facts_agent import facts_agent
from utils.agents.C_source_classifier.source_class_agent import source_class_agent
from utils.agents.D_report_agent.report_agent import report_agent


def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("search", search_agent)
    graph.add_node("facts", facts_agent)
    graph.add_node("source_classification", source_class_agent)
    graph.add_node("report", report_agent)


    graph.set_entry_point("search")
    graph.add_edge("search", "facts")
    graph.add_edge("facts", "source_classification")
    graph.add_edge("source_classification", "report")
    graph.add_edge("report", END)
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


