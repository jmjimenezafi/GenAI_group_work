import os
from typing import Any, Dict
import httpx
from bs4 import BeautifulSoup
from tavily import TavilyClient
from utils.llm_service import get_llm
from utils.agents.workflow_models import ArticleState, WorkflowState

from utils.prompts import REFORMULATE_QUERY_PROMPT, REFORMULATE_QUERY_TEMPLATE


MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "10"))
TIMEOUT = int(os.getenv("SEARCH_TIMEOUT_SECONDS", "6"))
SEARCH_DEPTH = os.getenv("SEARCH_DEPTH", "advanced")
HEADERS = {"User-Agent": os.getenv("SEARCH_USER_AGENT", "gen-ai-trabajo/1.0")}


def _reformulate_query(query: str) -> str:
    llm = get_llm()
    user_query = REFORMULATE_QUERY_TEMPLATE.format(query=query)
    response = llm.invoke(
        [
            {"role": "system", "content": REFORMULATE_QUERY_PROMPT},
            {"role": "user", "content": user_query},
        ]
    )
    return response.content.strip()

def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]): # elimina etiquetas de código...
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())

def _get_article_text(
        url: str,
        client: httpx.Client,
        timeout_seconds: float,
) -> Dict[str, Any]:
    try:
        timeout = httpx.Timeout(
            timeout_seconds,
            connect=timeout_seconds,
            read=timeout_seconds,
            write=timeout_seconds,
        )
        response = client.get(url, timeout=timeout, follow_redirects=True)
    except httpx.RequestError:
        return {"url": url, "text": "", "error": "Request failed"}
    
    if response.status_code >= 400:
        return {"url": url, "text": "", "error": f"HTTP {response.status_code}"}
    
    content_type = response.headers.get("Content-Type", "")
    content_type_lower = content_type.lower()
    if "text/html" not in content_type_lower and "text/plain" not in content_type_lower:
        return {"url": url, "text": "", "error": f"unsupported_content_type: {content_type}"}

    html = response.text or ""
    text = _extract_text(html)
    return {
        "text": text,
        "content_type": content_type,
    }

def _iterate_results(
        items: list,
        client: httpx.Client,
        timeout_seconds: float
    ) -> list[ArticleState]:
    results = []
    for index, item in enumerate(items, start=1):
        url = (item.get("url") or "").strip()
        entry = {
            "index": index,
            "url": url,
            "title": (item.get("title") or "").strip(),
            "snippet": (item.get("content") or "").strip(),
            "status": "skipped",
        }
        if not url:
            entry["error"] = "missing_url"
        else:
            fetch_result = _get_article_text(url, client, timeout_seconds)
            if "error" in fetch_result:
                entry["error"] = fetch_result["error"]
            else:
                entry["status"] = "fetched"
                entry["text"] = fetch_result.get("text", "")
                entry["content_type"] = fetch_result.get("content_type", "")
        results.append(ArticleState(**entry))
    return results


def search_news(
    query: str,
    max_results: int = MAX_RESULTS,
    timeout_seconds: float = TIMEOUT,
) -> WorkflowState:
    clean_query = query.strip()
    if not clean_query:
        raise ValueError("La query no puede estar vacía")
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY no configurada en el entorno")
    
    if max_results <= 0:
        raise ValueError("El número de resultados máximos debe ser un número positivo")
    if timeout_seconds <= 0:
        raise ValueError("El tiempo de espera debe ser un número positivo") 
    
    reformulated_query = _reformulate_query(clean_query)
    tavily_client = TavilyClient(api_key=api_key)
    search_results = tavily_client.search(
        reformulated_query,
        max_results=max_results,
        search_depth=SEARCH_DEPTH,
    )
    items = search_results.get("results") or search_results.get("items") or []
    if not items and reformulated_query != clean_query:
        search_results = tavily_client.search(
            clean_query,
            max_results=max_results,
            search_depth=SEARCH_DEPTH,
        )
        items = search_results.get("results") or search_results.get("items") or []
        reformulated_query = clean_query

    with httpx.Client(headers=HEADERS) as client:
        articles = _iterate_results(items, client, timeout_seconds)
    return WorkflowState(
        query=clean_query,
        reformulated_query=reformulated_query,
        articles=articles,
        total_results=len(articles),
    )



