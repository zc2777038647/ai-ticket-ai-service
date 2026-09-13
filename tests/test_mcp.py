from app.services.mcp_server import search_ticket_knowledge


def test_mcp_search_tool_returns_source_metadata() -> None:
    result = search_ticket_knowledge("security ticket", 2)
    assert result
    assert all("source" in item and "snippet" in item for item in result)
