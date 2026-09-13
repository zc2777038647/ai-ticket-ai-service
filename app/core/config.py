from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AI_", env_file=".env", extra="ignore")

    service_host: str = "127.0.0.1"
    service_port: int = 8000
    internal_token: str = "dev-internal-token"
    java_base_url: str = "http://localhost:8080"
    java_internal_token: str = "dev-internal-token"
    provider_mode: str = "fake"
    provider_base_url: str = "https://api.openai.com/v1"
    provider_api_key: str | None = None
    model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 15.0
    llm_retry_count: int = 1
    rag_top_k: int = 2
    agent_max_tool_calls: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()
