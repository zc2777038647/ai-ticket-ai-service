from typing import Any

import httpx

from app.core.config import Settings
from app.models.schemas import JavaHistoryEvent, JavaTicket


class JavaToolError(RuntimeError):
    pass


class JavaTicketToolClient:
    """Read-only adapter; Python never receives database credentials."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client

    async def _get(self, path: str) -> Any:
        headers = {"X-Internal-AI-Token": self._settings.java_internal_token}
        try:
            if self._client is not None:
                response = await self._client.get(
                    f"{self._settings.java_base_url.rstrip('/')}{path}", headers=headers
                )
            else:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        f"{self._settings.java_base_url.rstrip('/')}{path}", headers=headers
                    )
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise JavaToolError(f"Java read-only tool failed: {type(exc).__name__}") from exc

    async def get_ticket_detail(self, ticket_id: int) -> JavaTicket:
        return JavaTicket.model_validate(await self._get(f"/internal/ai/tickets/{ticket_id}"))

    async def get_ticket_history(self, ticket_id: int) -> list[JavaHistoryEvent]:
        data = await self._get(f"/internal/ai/tickets/{ticket_id}/history")
        return [JavaHistoryEvent.model_validate(item) for item in data]
