from langchain_core.messages import HumanMessage

from src.app.ai_providers.schemas import SupportedModels
from app.utils.ai import create_chat_model, invoke_chat_model
from src.app.core.exceptions import InvalidAPIKeyException, UnsupportedProviderException

class AIProvidersService:
    """
    Service for managing AI providers and their supported models.
    """

    def __init__(self, supported_models):
        self.supported_models: SupportedModels = supported_models

    def get_supported_models(self) -> SupportedModels:
        """
        Return a dictionary of supported models grouped by provider.
        """
        return self.supported_models.model_dump()

    def validate_api_key(self, api_key: str) -> None:
        """
        Basic validation of a user-supplied API key.
        """
        if not api_key or not isinstance(api_key, str) or len(api_key.strip()) == 0:
            raise InvalidAPIKeyException(message="API key is missing or invalid.")

        if len(api_key.strip()) < 10:
            raise InvalidAPIKeyException(message="API key is too short to be valid.")

    def validate_provider_model(self, provider: str, model: str) -> None:
        """
        Validate that the given provider and model are supported.
        Raises UnsupportedProviderException if not supported.
        """
        if provider not in self.supported_models.model_dump():
            raise UnsupportedProviderException(
                message=f"Provider '{provider}' is not supported."
            )

        if model not in self.supported_models.model_dump().get(provider, []):
            raise UnsupportedProviderException(
                message=f"Model '{model}' is not supported for provider '{provider}'."
            )

    async def check_provider_connection(
        self, 
        provider: str, 
        model: str, 
        api_key: str
    ) -> bool:
        """
        Check if the connection to the specified provider is valid using the provided API key.
        """
        # Validate the API key format - Basic validation
        self.validate_api_key(api_key)

        # Check if the provider and model are supported
        self.validate_provider_model(provider, model)

        llm = create_chat_model(provider, model, api_key)
        response = await invoke_chat_model(
            llm,
            [HumanMessage("Reply with the word OK.")],
        )

        return response