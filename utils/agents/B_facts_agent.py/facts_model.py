from pydantic import BaseModel, Field

class ArticleSummary(BaseModel):
    summary: str = Field(description="2-4 sentence summary of the article")
    facts: list[str] = Field(description="Key verifiable facts from the article")