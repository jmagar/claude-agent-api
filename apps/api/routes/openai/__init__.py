"""OpenAI-compatible API routes."""

from apps.api.routes.openai.assistants import router as assistants_router
from apps.api.routes.openai.chat import router as chat_router
from apps.api.routes.openai.models import router as models_router
from apps.api.routes.openai.threads import router as threads_router

__all__ = [
    "assistants_router",
    "chat_router",
    "models_router",
    "threads_router",
]
