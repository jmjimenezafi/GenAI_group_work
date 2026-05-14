import logging

from utils.agents.workflow_models import WorkflowState
from utils.agents.C_source_classifier.source_class_service import classify_sources
LOGGING = logging.getLogger(__name__)


def source_class_agent(workflow_state: WorkflowState) -> WorkflowState:
    query = workflow_state.query or ""
    LOGGING.info("Source classification agent started for query: %s", query)
    try:
        workflow_state.articles = classify_sources(workflow_state.articles)
    except Exception as e:
        LOGGING.error("Error occurred while classifying sources: %s", str(e))
        workflow_state.errors.append(str(e))
    return workflow_state