from utils.agents.workflow_models import ArticleState, SourceClassification, WorkflowState
from utils.llm_service import get_llm
from utils.prompts import REPORT_SYSTEM_PROMPT, REPORT_USER_TEMPLATE


def _format_source(classification: SourceClassification | None) -> str:
    if not classification:
        return "tipo=desconocido; sesgo=desconocido; alcance=desconocido; idioma=desconocido; confianza=desconocida"
    notes = f"; notas={classification.notas}" if classification.notas else ""
    return (
        f"tipo={classification.tipo_fuente or 'desconocido'}; "
        f"sesgo={classification.senal_sesgo or 'desconocido'}; "
        f"alcance={classification.alcance_geografico or 'desconocido'}; "
        f"idioma={classification.idioma_principal or 'desconocido'}; "
        f"confianza={classification.confianza or 'desconocida'}"
        f"{notes}"
    )


def _format_article(article: ArticleState, index: int) -> str:
    facts = article.facts or []
    facts_block = "\n".join(f"- {fact}" for fact in facts) or "- (sin hechos)"
    summary = article.summary or "(sin resumen)"
    title = article.title or "(sin titulo)"
    source_line = _format_source(article.source_classification)
    return "\n".join(
        [
            f"Articulo {index}:",
            f"Titulo: {title}",
            f"URL: {article.url}",
            f"Resumen: {summary}",
            "Hechos:",
            facts_block,
            f"Fuente: {source_line}",
        ]
    )


def _build_articles_info(articles: list[ArticleState]) -> str:
    if not articles:
        return "Sin articulos disponibles."
    return "\n\n".join(
        _format_article(article, index) for index, article in enumerate(articles, start=1)
    )


def generate_report_markdown(state: WorkflowState) -> str:
    llm = get_llm()
    query = state.query or ""
    articles_info = _build_articles_info(state.articles)
    fact_cross_check = state.fact_cross_check or "No disponible."
    user_prompt = REPORT_USER_TEMPLATE.format(
        query=query,
        articles_info=articles_info,
        fact_cross_check=fact_cross_check,
    )
    response = llm.invoke([
        ("system", REPORT_SYSTEM_PROMPT),
        ("user", user_prompt),
    ])
    return response.content.strip()


def report_agent(state: WorkflowState) -> WorkflowState:
    state.report_markdown = generate_report_markdown(state)
    return state
