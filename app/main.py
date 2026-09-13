from pathlib import Path

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.services.agent import TicketAgent
from app.services.providers import build_provider
from app.services.rag import KnowledgeRetriever
from app.services.tools import JavaTicketToolClient


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AI Ticket Service", version="0.1.0")
    knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"
    retriever = KnowledgeRetriever(knowledge_dir)
    app.state.settings = settings
    app.state.provider = build_provider(settings)
    app.state.retriever = retriever
    app.state.agent = TicketAgent(settings, retriever, JavaTicketToolClient(settings))
    app.include_router(router)

    return app


app = create_app()
