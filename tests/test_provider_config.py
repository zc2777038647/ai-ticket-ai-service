import pytest

from app.core.config import Settings
from app.services.providers import (
    FakeTicketAiProvider,
    OpenAICompatibleTicketAiProvider,
    ProviderError,
    build_provider,
)


def test_provider_mode_selects_fake_provider() -> None:
    assert isinstance(build_provider(Settings(provider_mode="fake")), FakeTicketAiProvider)


def test_openai_mode_requires_external_credential() -> None:
    with pytest.raises(ProviderError, match="provider_api_key"):
        build_provider(Settings(provider_mode="openai"))


def test_unknown_provider_mode_fails_closed() -> None:
    with pytest.raises(ProviderError, match="unsupported provider mode"):
        build_provider(Settings(provider_mode="unknown"))
