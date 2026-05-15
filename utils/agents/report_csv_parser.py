from pathlib import Path

import pandas as pd
from pydantic import BaseModel

from utils.agents.workflow_models import WorkflowState
from utils.llm_service import get_llm


class ReportCSVRow(BaseModel):
    claim: str
    veracity: str
    reasoning: str
    urls: list[str]


def parse_report_csv(state: WorkflowState, output_path: str | Path | None = None) -> Path:
    report_markdown = state.report_markdown or ""
    if not report_markdown.strip():
        raise ValueError("report_markdown is empty")

    structured_llm = get_llm().with_structured_output(
        ReportCSVRow,
        method="function_calling",
    )

    result = structured_llm.invoke([
        (
            "system",
            "Eres un asistente que extrae datos estructurados de un reporte en markdown. "
            "Devuelve claim (texto exacto de la afirmacion), veracity (Apoya, Contradice, No concluyente), "
            "reasoning (justificacion breve) y urls (lista de URLs citadas).",
        ),
        (
            "user",
            "Analiza el siguiente reporte y extrae los campos solicitados:\n\n"
            + report_markdown,
        ),
    ])

    urls = [url.strip() for url in (result.urls or []) if url and url.strip()]
    row = {
        "claim": result.claim.strip(),
        "veracity": result.veracity.strip(),
        "reasoning": result.reasoning.strip(),
        "urls": "; ".join(urls),
    }
    df = pd.DataFrame([row])

    if output_path is None:
        repo_root = Path(__file__).resolve().parents[2]
        output_path = repo_root / "data" / "new_claims.csv"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path