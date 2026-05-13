from utils.llm_service import get_llm
from utils.agents.workflow_models import ArticleState, SourceClassification
from utils.prompts import SOURCE_CLASSIFIER_SYSTEM_PROMPT, SOURCE_CLASSIFIER_USER_TEMPLATE


def _classify_source(url: str) -> SourceClassification:
    llm = get_llm()
    user_prompt = SOURCE_CLASSIFIER_USER_TEMPLATE.format(url=url)
    structured_llm = llm.with_structured_output(SourceClassification)
    result: SourceClassification = structured_llm.invoke([
        ("system", SOURCE_CLASSIFIER_SYSTEM_PROMPT),
        ("user", user_prompt),
    ])
    if not result.url:
        result.url = url
    return result


def classify_sources(items: list[ArticleState]) -> list[ArticleState]:
    for article in items:
        if not article.url:
            continue
        article.source_classification = _classify_source(article.url)
    return items