from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, field_validator


def _to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True, extra="forbid")


class TicketPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class HealthResponse(ApiModel):
    status: str
    service: str


class TicketAnalysisRequest(ApiModel):
    ticket_id: PositiveInt
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=2000)
    current_priority: TicketPriority

    @field_validator("title", "description")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class TicketAnalysisResult(ApiModel):
    category: str = Field(min_length=1, max_length=64)
    suggested_priority: TicketPriority
    reason: str = Field(min_length=1, max_length=1000)
    confidence: float = Field(ge=0.0, le=1.0)


class TicketReplyDraftRequest(ApiModel):
    ticket_id: PositiveInt
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=2000)
    creator_name: str = Field(min_length=1, max_length=64)


class TicketReplyDraftResult(ApiModel):
    draft: str = Field(min_length=1, max_length=4000)
    tone: str = Field(min_length=1, max_length=32)


class JavaTicket(ApiModel):
    id: PositiveInt
    title: str
    description: str
    creator_name: str
    priority: TicketPriority
    status: str


class JavaHistoryEvent(ApiModel):
    id: PositiveInt
    ticket_id: PositiveInt
    operator_user_id: PositiveInt
    operation_type: str
    before_value: str | None = None
    after_value: str | None = None
    created_at: str | None = None


class SourceCitation(ApiModel):
    source: str
    snippet: str


class AgentRequest(ApiModel):
    ticket_id: PositiveInt
    query: str = Field(min_length=1, max_length=1000)

    @field_validator("query")
    @classmethod
    def query_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class AgentResponse(ApiModel):
    answer: str
    sources: list[SourceCitation]
    tool_calls: int = Field(ge=0)


class RAGSearchRequest(ApiModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=10)


class RAGSearchResponse(ApiModel):
    results: list[SourceCitation]
