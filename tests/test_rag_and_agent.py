import asyncio
from pathlib import Path

from app.core.config import Settings
from app.models.schemas import AgentRequest, JavaHistoryEvent, JavaTicket, TicketPriority
from app.services.agent import TicketAgent
from app.services.rag import KnowledgeRetriever


def test_rag_top_k_changes_number_of_results() -> None:
    retriever = KnowledgeRetriever(Path("knowledge"))
    one = retriever.search("priority support", 1)
    three = retriever.search("priority support", 3)
    assert len(one) == 1
    assert len(three) >= len(one)
    assert len(three) <= 3


class FakeJavaTools:
    async def get_ticket_detail(self, ticket_id: int) -> JavaTicket:
        return JavaTicket(
            id=ticket_id,
            title="Login failure",
            description="Cannot login",
            creatorName="demo",
            priority=TicketPriority.HIGH,
            status="OPEN",
        )

    async def get_ticket_history(self, ticket_id: int) -> list[JavaHistoryEvent]:
        return []


def test_agent_uses_allowlisted_read_only_tool_and_rag() -> None:
    settings = Settings(agent_max_tool_calls=3, rag_top_k=1)
    agent = TicketAgent(settings, KnowledgeRetriever(Path("knowledge")), FakeJavaTools())
    result = asyncio.run(agent.run(AgentRequest(ticketId=7, query="What is the priority guidance?")))
    assert result.tool_calls == 1
    assert result.sources
    assert "Ticket 7" in result.answer
