import logging

from utils.agents.workflow_models import WorkflowState
from utils.agents.D_report_agent.report_service import generate_report_markdown
LOGGING = logging.getLogger(__name__)


def report_agent(workflow_state: WorkflowState) -> WorkflowState:
    query = workflow_state.query or ""
    LOGGING.info("Report agent started for query: %s", query)
    try:
        workflow_state.report_markdown = generate_report_markdown(workflow_state)
    except Exception as e:
        LOGGING.error("Error occurred while generating report: %s", str(e))
        workflow_state.report_markdown = "Error occurred while generating report."
        workflow_state.errors.append(str(e))
    return workflow_state
