import os

import logging
from typing import Any, Dict, TypedDict

from utils.agents.A_websearch_agent.websearch_service import search_news


LOGGER = logging.getLogger(__name__)

class SearchState(TypedDict, total=False):
    query: str
    results: list[Dict[str, Any]],
    error: str

def search_agent(query: str) -> SearchState:
    LOGGER.info("Searching agent started with query: %s", query)
    try:
        results = search_news(query)
    except Exception as e:
        LOGGER.error("Error occurred while searching: %s", e)
        return SearchState(query=query, error=str(e))
    
    total_results = results.get("total_results", 0)
    LOGGER.info("Search completed with %d total results", total_results)
    return SearchState(query=query, results=results)