from src.app.ai_providers.service import AIProvidersService
from src.app.ai_providers.ai_providers_models import SUPPORTED_MODELS

def get_ai_providers_service() -> AIProvidersService:
    return AIProvidersService(
        supported_models=SUPPORTED_MODELS
    )
