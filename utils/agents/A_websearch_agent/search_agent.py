import os

import logging

from utils.agents.A_websearch_agent.websearch_service import search_news
from utils.agents.workflow_models import WorkflowState


LOGGER = logging.getLogger(__name__)

def search_agent(query: str) -> WorkflowState:
    LOGGER.info("Searching agent started with query: %s", query)
    try:
        state = search_news(query)
    except Exception as e:
        LOGGER.error("Error occurred while searching: %s", e)
        return WorkflowState(query=query, errors=[str(e)])

    total_results = state.total_results
    if total_results is None:
        total_results = len(state.articles)
    LOGGER.info("Search completed with %d total results", total_results)
    return state