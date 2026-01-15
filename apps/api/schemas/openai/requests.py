"""OpenAI-compatible request Pydantic schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class OpenAIMessage(BaseModel):
    """Message object for chat completion requests."""

    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    """Chat completion request schema.

    Validates incoming OpenAI-compatible chat completion requests.
    """

    model: str = Field(..., min_length=1)
    messages: list[OpenAIMessage] = Field(..., min_length=1)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = None
    top_p: float | None = None
    stop: list[str] | str | None = None
    stream: bool = False
    user: str | None = None
