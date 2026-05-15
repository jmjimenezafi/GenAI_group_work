import logging
import atexit

from utils.llm_service import get_llm
from utils.prompts import RAG_SYSTEM_PROMPT, RAG_SYSTEM_TEMPLATE
from utils.rag.qdrant_service import QdrantService
from utils.agents.workflow_models import RAGOutputDecision, WorkflowState
LOGGING = logging.getLogger(__name__)


# Usar un wrapper que recrea el cliente si es necesario
class LazyQdrantClient:
    def __init__(self):
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            self._client = QdrantService()
            atexit.register(self.close)
        return self._client
    
    def search(self, query: str):
        return self._get_client().search(query)
    
    def close(self):
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None


client = LazyQdrantClient()

def _retrieve_past_claims(query: str) -> list[str]:
    try:
        results = client.search(query)
        try:
            points = results.points
        except AttributeError:
            points = results
        if not points:
            return ["Sin claims previos relevantes."]


        claims = []
        for point in points:
            if isinstance(point, dict):
                payload = point.get("payload", point)
                point_id = point.get("id")
            else:
                payload = point.payload
                point_id = point.id
            urls = payload.get("urls") if isinstance(payload, dict) else None
            if isinstance(urls, list):
                urls_text = ", ".join(urls)
            else:
                urls_text = urls or "sin URL"
            claims.append(
                "\n".join(
                    [
                        f"Claim ID: {point_id or 'unknown'} - {payload.get('claim', 'sin texto')}",
                        f"Veredicto: {payload.get('veracity', 'desconocido')}",
                        f"Razon: {payload.get('reasoning', 'sin razon')}",
                        f"(Fuentes: {urls_text})",
                    ]
                )
            )
        return claims
    except Exception as e:
        LOGGING.error("Error retrieving past claims: %s", str(e))
        return [f"Error retrieving past claims: {str(e)}"]

def rag_agent(state: WorkflowState) -> WorkflowState:
    LOGGING.info("RAG agent started for query: %s", state.query)
    query = state.query or ""
    state.past_claims = _retrieve_past_claims(query)
    llm = get_llm()
    try:
        structured_llm = llm.with_structured_output(
            RAGOutputDecision,
            method="function_calling",
        )
        LOGGING.info("Invoking RAG decision LLM for query: %s", query)
        state.rag_response = structured_llm.invoke([
            ("system", RAG_SYSTEM_PROMPT),
            ("user", RAG_SYSTEM_TEMPLATE.format(query=query, articles_info="\n\n".join(state.past_claims))),
        ])
        LOGGING.info(f"RAG decision LLM completed - RAG Response:\n\nCan Answer: {state.rag_response.can_answer}\nReasoning: {state.rag_response.reasoning}\nRelevant Articles: {state.rag_response.relevant_articles}")
    except Exception as e:
        LOGGING.error("Error during RAG processing: %s", str(e))
        state.rag_response = RAGOutputDecision(
            can_answer=False,
            relevant_articles=None,
            reasoning=f"Error during RAG processing: {str(e)}",
        )
        state.errors.append(str(e))
    return state




