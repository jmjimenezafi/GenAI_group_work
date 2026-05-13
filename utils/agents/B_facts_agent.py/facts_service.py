import os
from typing import List

from utils.llm_service import get_llm
from utils.agents.workflow_models import ArticleState, ArticleSummary
from utils.prompts import ARTICLE_SUMMARY_SYSTEM_PROMPT, ARTICLE_SUMMARY_USER_TEMPLATE, FACT_CROSS_CHECK_SYSTEM_PROMPT, FACT_CROSS_CHECK_TEMPLATE

MAX_DOC_CHARS = int(os.getenv("FACTS_MAX_DOC_CHARS", "4000"))
MAX_ARTICLE_FACTS = int(os.getenv("FACTS_MAX_ARTICLE_FACTS", "6"))

def _build_article_summary(item: ArticleState, llm) -> ArticleState | None:
    if item.status != "fetched":
        return None
    url = item.url
    title = item.title or ""
    text = item.text or ""
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
    item.summary = result.summary
    item.facts = result.facts[:MAX_ARTICLE_FACTS]
    return item


def summarize_articles(items: List[ArticleState]) -> List[ArticleState]:  # debe recibir la lista que salga del search_news
    llm = get_llm()
    for item in items:
        _build_article_summary(item, llm)
    return items



def _build_fact_check_prompt(summaries: List[ArticleState]) -> str:
    fact_base_prompt = FACT_CROSS_CHECK_SYSTEM_PROMPT + "\n\n"
    for i, summary in enumerate(summaries):
        title = summary.title or ""
        url = summary.url
        summary_text = summary.summary or ""
        fact_base_prompt += (
            f"Article {i+1}:\nTitle: {title}\nURL: {url}\nSummary: {summary_text}\nFacts:\n"
        )
        for fact in summary.facts:
            fact_base_prompt += f"- {fact}\n"
        fact_base_prompt += "\n"
    return fact_base_prompt

def fact_cross_check(summaries: List[ArticleState]) -> str:
    llm = get_llm()
    fact_check_prompt = _build_fact_check_prompt(summaries)
    response = llm.invoke(
        [{"system": fact_check_prompt,
          "user": FACT_CROSS_CHECK_TEMPLATE.format(articles_info = fact_check_prompt)}]
    )

    return response.content.strip()

