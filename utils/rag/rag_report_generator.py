import logging

from utils.agents.workflow_models import WorkflowState
from utils.llm_service import get_llm
from utils.prompts import RAG_REPORT_SYSTEM_PROMPT, RAG_REPORT_USER_TEMPLATE

LOGGING = logging.getLogger(__name__)


def generate_rag_report(state: WorkflowState) -> str:
    llm = get_llm()
    query = state.query or ""
    rag_response = state.rag_response or "Sin decision RAG disponible."
    past_claims = "\n\n".join(state.past_claims or []) or "Sin claims previos relevantes."
    user_prompt = RAG_REPORT_USER_TEMPLATE.format(
        query=query,
        rag_response=rag_response,
        past_claims=past_claims,
    )
    LOGGING.info("Invoking RAG report LLM for query: %s", query)
    response = llm.invoke([
        ("system", RAG_REPORT_SYSTEM_PROMPT),
        ("user", user_prompt),
    ])
    return response.content.strip()


def rag_report_agent(state: WorkflowState) -> WorkflowState:
    state.report_markdown = generate_rag_report(state)
    LOGGING.info("RAG report generated for query: %s", state.query)
    return state
from utils.agents.workflow_models import WorkflowState
from utils.llm_service import get_llm
from utils.prompts import RAG_REPORT_SYSTEM_PROMPT, RAG_REPORT_USER_TEMPLATE


def generate_rag_report(state: WorkflowState) -> str:
    llm = get_llm()
    query = state.query or ""
    rag_response = state.rag_response or "Sin decision RAG disponible."
    past_claims = "\n\n".join(state.past_claims or []) or "Sin claims previos relevantes."
    user_prompt = RAG_REPORT_USER_TEMPLATE.format(
        query=query,
        rag_response=rag_response,
        past_claims=past_claims,
    )
    response = llm.invoke([
        ("system", RAG_REPORT_SYSTEM_PROMPT),
        ("user", user_prompt),
    ])
    return response.content.strip()


def rag_report_agent(state: WorkflowState) -> WorkflowState:
    LOGGING.info("RAG report agent started for query: %s", state.query)
    state.report_markdown = generate_rag_report(state)
    return state
