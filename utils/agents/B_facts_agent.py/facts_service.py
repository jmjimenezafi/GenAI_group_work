import os
from typing import Any, Dict, List, Tuple

from utils.llm_service import get_llm
from utils.agents.B_facts_agent.facts_model import ArticleSummary
from utils.prompts import ARTICLE_SUMMARY_SYSTEM_PROMPT, ARTICLE_SUMMARY_USER_TEMPLATE, FACT_CROSS_CHECK_SYSTEM_PROMPT, FACT_CROSS_CHECK_TEMPLATE

MAX_DOC_CHARS = int(os.getenv("FACTS_MAX_DOC_CHARS", "4000"))
MAX_ARTICLE_FACTS = int(os.getenv("FACTS_MAX_ARTICLE_FACTS", "6"))

def _build_article_summary(item: dict, llm) -> dict | None:
    if item.get("status") != "fetched":
        return None
    url = item.get("url", "")
    title = item.get("title", "")
    text = item.get("text", "")
    if not text:
        return None

    structured_llm = llm.with_structured_output(ArticleSummary) #  pasamos el llm como argumento para no iniciar en cada articulo
    user_prompt = ARTICLE_SUMMARY_USER_TEMPLATE.format(
        title=title, url=url, text=text[:MAX_DOC_CHARS] # limitamos el texto para no superar el maximo de caracteres permitido por el modelo
    )
    result: ArticleSummary = structured_llm.invoke([
        ("system", ARTICLE_SUMMARY_SYSTEM_PROMPT),
        ("user", user_prompt),
    ])
    return {"url": url, "title": title, "summary": result.summary, "facts": result.facts[:MAX_ARTICLE_FACTS]}


def summarize_articles(items: List[dict]) -> List[dict]: # debe recibir la lista que salga del search_news
    llm = get_llm()
    summaries = []
    for item in items:
        summary = _build_article_summary(item, llm)
        if summary:
            summaries.append(summary)
    return summaries



def _build_fact_check_prompt(summaries: List[dict]) -> str:
    fact_base_prompt = FACT_CROSS_CHECK_SYSTEM_PROMPT + "\n\n"
    for i, summary in enumerate(summaries):
        fact_base_prompt += f"Article {i+1}:\nTitle: {summary['title']}\nURL: {summary['url']}\nSummary: {summary['summary']}\nFacts:\n"
        for fact in summary["facts"]:
            fact_base_prompt += f"- {fact}\n"
        fact_base_prompt += "\n"
    return fact_base_prompt

def fact_cross_check(summaries: List[dict]) -> List[Dict[str, Any]]:
    llm = get_llm()
    results = []
    fact_check_prompt = _build_fact_check_prompt(summaries)
    response = llm.invoke(
        [{"system": fact_check_prompt,
          "user": FACT_CROSS_CHECK_TEMPLATE.format(articles_info = fact_check_prompt)}]
    )

    return response.content.strip

