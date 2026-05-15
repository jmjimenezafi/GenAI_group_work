import logging

from utils.agents.A_websearch_agent.websearch_service import search_news
from utils.agents.workflow_models import WorkflowState


LOGGER = logging.getLogger(__name__)

def search_agent(state: WorkflowState) -> WorkflowState:
    query = state.query or ""
    LOGGER.info("Searching agent started with query: %s", query)
    try:
        search_state = search_news(query)
    except Exception as e:
        LOGGER.error("Error occurred while searching: %s", e)
        state.errors.append(str(e))
        return state

    state.reformulated_query = search_state.reformulated_query
    state.articles = search_state.articles
    state.total_results = search_state.total_results
    if search_state.errors:
        state.errors.extend(search_state.errors)

    total_results = state.total_results
    if total_results is None:
        total_results = len(state.articles)
        state.total_results = total_results
    LOGGER.info("Search completed with %d total results", total_results)
    return state