import logging

from utils.agents.workflow_models import WorkflowState
from utils.agents.B_facts_agent.facts_service import fact_cross_check, summarize_articles


LOGGING = logging.getLogger(__name__)


def facts_agent(workflow_state: WorkflowState) -> WorkflowState:
    query = workflow_state.query or ""
    LOGGING.info("Facts agent started for query: %s", query)
    workflow_state.articles = summarize_articles(workflow_state.articles)
    try:
        workflow_state.fact_cross_check = fact_cross_check(workflow_state.articles)
    except Exception as e:
        LOGGING.error("Error occurred while checking facts: %s", str(e))
        workflow_state.fact_cross_check = "Error occurred while checking facts."
        workflow_state.errors.append(str(e))
    return workflow_state