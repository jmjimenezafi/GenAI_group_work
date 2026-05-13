from __future__ import annotations

from pydantic import BaseModel, Field

try:
    from pydantic import ConfigDict
except ImportError:  # pydantic v1
    ConfigDict = None


class _BaseStateModel(BaseModel):
    if ConfigDict:
        model_config = ConfigDict(extra="allow")
    else:
        class Config:
            extra = "allow"


class ArticleSummary(BaseModel):
    summary: str = Field(description="2-4 sentence summary of the article")
    facts: list[str] = Field(description="Key verifiable facts from the article")


class SourceClassification(_BaseStateModel):
    url: str | None = None
    domain: str | None = None
    tipo_fuente: str | None = None
    senal_sesgo: str | None = None
    alcance_geografico: str | None = None
    idioma_principal: str | None = None
    confianza: str | None = None
    notas: str | None = None


class ArticleState(_BaseStateModel):
    url: str
    title: str | None = None
    snippet: str | None = None
    text: str | None = None
    status: str | None = None
    error: str | None = None
    content_type: str | None = None

    summary: str | None = None
    facts: list[str] = Field(default_factory=list)
    source_classification: SourceClassification | None = None


class WorkflowState(_BaseStateModel):
    query: str | None = None
    reformulated_query: str | None = None
    articles: list[ArticleState] = Field(default_factory=list)
    total_results: int | None = None
    fact_cross_check: str | None = None
    report_markdown: str | None = None
    errors: list[str] = Field(default_factory=list)


def coerce_article(item: ArticleState | dict) -> ArticleState:
    if isinstance(item, ArticleState):
        return item
    return ArticleState(**item)