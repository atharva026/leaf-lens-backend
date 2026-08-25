import asyncio
from typing import Any

from langchain.chat_models import BaseChatModel, init_chat_model

from src.app.core.config import config
from src.app.core.exceptions import (
    AIRequestTimeoutException,
    InvalidAPIKeyException,
    UnsupportedProviderException,
)
from src.app.core.logging import get_logger

logger = get_logger(__name__)

def create_chat_model(provider: str, model: str, api_key: str) -> BaseChatModel | None:
    """Create a LangChain chat model with the application timeout."""
    try:
        return init_chat_model(
            model=model,
            model_provider=provider,
            api_key=api_key,
            timeout=config.AI_REQUEST_TIMEOUT_SECONDS,
        )
    except Exception as error:
        logger.error("Failed to init chat model %s:%s - %s", provider, model, error)
        raise UnsupportedProviderException(
            message=f"Could not initialize model '{model}' for provider '{provider}'"
        )

async def invoke_chat_model(model: Any, messages: list[Any]) -> Any:
    """Invoke a LangChain chat model and map common provider failures."""
    try:
        # Application-level timeout for AI requests, to avoid hanging indefinitely on provider issues.
        return await asyncio.wait_for(
            model.ainvoke(messages),
            timeout=config.AI_REQUEST_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.error(
            "AI request timed out after %ss", config.AI_REQUEST_TIMEOUT_SECONDS
        )
        raise AIRequestTimeoutException()
    except Exception as error:
        # Covers provider-side auth errors (bad key), rate limits, etc.
        logger.error("AI provider error: %s", error)
        message = str(error).lower()
        if (
            "auth" in message
            or "api key" in message
            or "unauthorized" in message
            or "401" in message
        ):
            raise InvalidAPIKeyException(message="API key rejected by provider")
        raise