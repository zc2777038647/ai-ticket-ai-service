from pathlib import Path

from mcp.server.fastmcp import FastMCP

from app.services.rag import KnowledgeRetriever


_retriever = KnowledgeRetriever(Path(__file__).resolve().parents[2] / "knowledge")
mcp = FastMCP("ai-ticket-knowledge")


@mcp.tool()
def search_ticket_knowledge(query: str, top_k: int = 2) -> list[dict[str, str]]:
    """Search the local support knowledge base; this tool is read-only."""
    return [item.model_dump() for item in _retriever.search(query, top_k)]


if __name__ == "__main__":
    mcp.run(transport="stdio")
