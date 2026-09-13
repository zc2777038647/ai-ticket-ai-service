from fastapi import APIRouter, Header, HTTPException, Request, status

from app.models.schemas import (
    AgentRequest,
    AgentResponse,
    HealthResponse,
    RAGSearchRequest,
    RAGSearchResponse,
    TicketAnalysisRequest,
    TicketAnalysisResult,
    TicketReplyDraftRequest,
    TicketReplyDraftResult,
)
from app.services.providers import ProviderError
from app.services.tools import JavaToolError


router = APIRouter()


def require_internal_token(request: Request, token: str | None) -> None:
    if token != request.app.state.settings.internal_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid internal token")


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="UP", service="ai-ticket-ai-service")


@router.post("/internal/ai/ticket-analysis", response_model=TicketAnalysisResult)
async def analyze_ticket(
    payload: TicketAnalysisRequest,
    request: Request,
    x_internal_ai_token: str | None = Header(default=None),
) -> TicketAnalysisResult:
    require_internal_token(request, x_internal_ai_token)
    try:
        return await request.app.state.provider.analyze(payload)
    except ProviderError as exc:
        code = status.HTTP_502_BAD_GATEWAY if exc.invalid_output else status.HTTP_503_SERVICE_UNAVAILABLE
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.post("/internal/ai/ticket-reply-draft", response_model=TicketReplyDraftResult)
async def draft_reply(
    payload: TicketReplyDraftRequest,
    request: Request,
    x_internal_ai_token: str | None = Header(default=None),
) -> TicketReplyDraftResult:
    require_internal_token(request, x_internal_ai_token)
    try:
        return await request.app.state.provider.draft_reply(payload)
    except ProviderError as exc:
        code = status.HTTP_502_BAD_GATEWAY if exc.invalid_output else status.HTTP_503_SERVICE_UNAVAILABLE
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.post("/internal/ai/agent", response_model=AgentResponse)
async def run_agent(
    payload: AgentRequest,
    request: Request,
    x_internal_ai_token: str | None = Header(default=None),
) -> AgentResponse:
    require_internal_token(request, x_internal_ai_token)
    try:
        return await request.app.state.agent.run(payload)
    except JavaToolError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/internal/mcp/search", response_model=RAGSearchResponse)
async def mcp_search(
    payload: RAGSearchRequest,
    request: Request,
    x_internal_ai_token: str | None = Header(default=None),
) -> RAGSearchResponse:
    require_internal_token(request, x_internal_ai_token)
    top_k = payload.top_k or request.app.state.settings.rag_top_k
    return RAGSearchResponse(results=request.app.state.retriever.search(payload.query, top_k))
