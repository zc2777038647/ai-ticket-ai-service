from app.core.config import Settings
from app.models.schemas import AgentRequest, AgentResponse, SourceCitation
from app.services.rag import KnowledgeRetriever
from app.services.tools import JavaTicketToolClient


class TicketAgent:
    ALLOWED_TOOLS = frozenset({"get_ticket_detail", "get_ticket_history"})

    def __init__(self, settings: Settings, retriever: KnowledgeRetriever, tools: JavaTicketToolClient) -> None:
        self._settings = settings
        self._retriever = retriever
        self._tools = tools

    async def run(self, request: AgentRequest) -> AgentResponse:
        limit = self._settings.agent_max_tool_calls
        if limit < 1:
            raise RuntimeError("agent_max_tool_calls must be positive")

        ticket = await self._tools.get_ticket_detail(request.ticket_id)
        tool_calls = 1
        history = []
        if any(word in request.query.lower() for word in ("history", "log", "日志", "历史")):
            if tool_calls >= limit:
                raise RuntimeError("agent tool-call limit reached")
            history = await self._tools.get_ticket_history(request.ticket_id)
            tool_calls += 1

        sources = self._retriever.search(request.query, self._settings.rag_top_k)
        if history:
            sources = sources + [
                SourceCitation(
                    source="java:ticket-operation-history",
                    snippet=f"{len(history)} operation events for ticket {ticket.id}",
                )
            ]
        answer = (
            f"Ticket {ticket.id} is {ticket.status} with priority {ticket.priority}. "
            f"The controlled read-only agent reviewed the ticket and used {tool_calls} tool call(s)."
        )
        return AgentResponse(answer=answer, sources=sources, tool_calls=tool_calls)
