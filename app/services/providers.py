import json
from typing import Protocol

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.models.schemas import (
    TicketAnalysisRequest,
    TicketAnalysisResult,
    TicketReplyDraftRequest,
    TicketReplyDraftResult,
    TicketPriority,
)


class ProviderError(RuntimeError):
    def __init__(self, message: str, *, invalid_output: bool = False) -> None:
        super().__init__(message)
        self.invalid_output = invalid_output


class TicketAiProvider(Protocol):
    async def analyze(self, request: TicketAnalysisRequest) -> TicketAnalysisResult: ...

    async def draft_reply(self, request: TicketReplyDraftRequest) -> TicketReplyDraftResult: ...


class FakeTicketAiProvider:
    """Deterministic provider used for local development and contract tests."""

    async def analyze(self, request: TicketAnalysisRequest) -> TicketAnalysisResult:
        text = f"{request.title} {request.description}".lower()
        if any(word in text for word in ("密码", "登录", "account", "login", "password")):
            category = "ACCOUNT"
        elif any(word in text for word in ("支付", "账单", "payment", "billing")):
            category = "BILLING"
        elif any(word in text for word in ("故障", "错误", "down", "error", "outage")):
            category = "TECHNICAL"
        else:
            category = "GENERAL"

        priority = request.current_priority
        if any(word in text for word in ("紧急", "宕机", "urgent", "outage")):
            priority = TicketPriority.URGENT
        elif priority == TicketPriority.LOW and any(word in text for word in ("失败", "error", "错误")):
            priority = TicketPriority.MEDIUM

        return TicketAnalysisResult(
            category=category,
            suggested_priority=priority,
            reason="deterministic mock analysis; business data remains unchanged",
            confidence=0.9,
        )

    async def draft_reply(self, request: TicketReplyDraftRequest) -> TicketReplyDraftResult:
        return TicketReplyDraftResult(
            draft=(
                f"您好，已收到您关于“{request.title}”的问题。"
                "客服团队正在核查，我们会在确认后及时回复。"
            ),
            tone="professional",
        )


class OpenAICompatibleTicketAiProvider:
    """Provider adapter for an OpenAI-compatible structured JSON endpoint."""

    def __init__(self, settings: Settings) -> None:
        if not settings.provider_api_key:
            raise ProviderError("provider_api_key is required for openai mode")
        self._settings = settings

    async def _complete(self, system: str, user: str, schema_name: str) -> dict:
        url = f"{self._settings.provider_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self._settings.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self._settings.provider_api_key}"}
        attempts = max(1, self._settings.llm_retry_count + 1)
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                async with httpx.AsyncClient(timeout=self._settings.llm_timeout_seconds) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    body = response.json()
                    content = body["choices"][0]["message"]["content"]
                    return json.loads(content)
            except (httpx.HTTPError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt + 1 < attempts:
                    continue
        raise ProviderError(f"provider request failed: {last_error}") from last_error

    async def analyze(self, request: TicketAnalysisRequest) -> TicketAnalysisResult:
        data = await self._complete(
            "Return only JSON with category, suggestedPriority, reason, confidence. "
            "suggestedPriority must be LOW, MEDIUM, HIGH, or URGENT; confidence is 0..1.",
            request.model_dump_json(by_alias=True),
            "ticket_analysis",
        )
        try:
            return TicketAnalysisResult.model_validate(data)
        except ValidationError as exc:
            raise ProviderError("provider returned invalid analysis schema", invalid_output=True) from exc

    async def draft_reply(self, request: TicketReplyDraftRequest) -> TicketReplyDraftResult:
        data = await self._complete(
            "Return only JSON with draft and tone. The result is a human-reviewable draft, never a sent message.",
            request.model_dump_json(by_alias=True),
            "ticket_reply_draft",
        )
        try:
            return TicketReplyDraftResult.model_validate(data)
        except ValidationError as exc:
            raise ProviderError("provider returned invalid reply schema", invalid_output=True) from exc


def build_provider(settings: Settings) -> TicketAiProvider:
    if settings.provider_mode.lower() == "fake":
        return FakeTicketAiProvider()
    if settings.provider_mode.lower() in {"openai", "openai-compatible"}:
        return OpenAICompatibleTicketAiProvider(settings)
    raise ProviderError(f"unsupported provider mode: {settings.provider_mode}")
