from fastapi.testclient import TestClient

from app.main import app
from app.services.providers import ProviderError

TOKEN = "dev-internal-token"


def test_health_is_structured(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP", "service": "ai-ticket-ai-service"}


def test_internal_analysis_requires_token(client: TestClient) -> None:
    payload = {
        "ticketId": 10,
        "title": "Password reset",
        "description": "The user cannot log in",
        "currentPriority": "MEDIUM",
    }
    assert client.post("/internal/ai/ticket-analysis", json=payload).status_code == 401


def test_fake_analysis_is_structured_and_does_not_decide_business_state(client: TestClient) -> None:
    payload = {
        "ticketId": 10,
        "title": "Password reset",
        "description": "The user cannot log in",
        "currentPriority": "MEDIUM",
    }
    response = client.post(
        "/internal/ai/ticket-analysis",
        json=payload,
        headers={"X-Internal-AI-Token": TOKEN},
    )
    assert response.status_code == 200
    assert response.json() == {
        "category": "ACCOUNT",
        "suggestedPriority": "MEDIUM",
        "reason": "deterministic mock analysis; business data remains unchanged",
        "confidence": 0.9,
    }


def test_reply_draft_is_human_reviewable(client: TestClient) -> None:
    payload = {
        "ticketId": 10,
        "title": "Payment question",
        "description": "Please explain the invoice",
        "creatorName": "demo",
    }
    response = client.post(
        "/internal/ai/ticket-reply-draft",
        json=payload,
        headers={"X-Internal-AI-Token": TOKEN},
    )
    assert response.status_code == 200
    assert response.json()["tone"] == "professional"
    assert "已收到" in response.json()["draft"]


def test_provider_invalid_output_is_exposed_as_bad_gateway(client: TestClient) -> None:
    original = app.state.provider

    class InvalidProvider:
        async def analyze(self, request):
            raise ProviderError("invalid provider output", invalid_output=True)

        async def draft_reply(self, request):
            raise ProviderError("invalid provider output", invalid_output=True)

    app.state.provider = InvalidProvider()
    try:
        response = client.post(
            "/internal/ai/ticket-analysis",
            json={
                "ticketId": 10,
                "title": "Title",
                "description": "Description",
                "currentPriority": "HIGH",
            },
            headers={"X-Internal-AI-Token": TOKEN},
        )
        assert response.status_code == 502
        assert response.json()["detail"] == "invalid provider output"
    finally:
        app.state.provider = original


def test_mcp_search_requires_token_and_honors_top_k(client: TestClient) -> None:
    payload = {"query": "priority support", "topK": 1}
    assert client.post("/internal/mcp/search", json=payload).status_code == 401
    response = client.post(
        "/internal/mcp/search",
        json=payload,
        headers={"X-Internal-AI-Token": TOKEN},
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) <= 1
