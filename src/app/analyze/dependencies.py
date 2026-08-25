from fastapi import Depends

from src.app.analyze.service import AnalyzeService
from src.app.ai_providers.dependencies import get_ai_providers_service
from src.app.ai_providers.service import AIProvidersService

def get_analyze_service(
    ai_providers_service: AIProvidersService = Depends(get_ai_providers_service)
) -> AnalyzeService:
    return AnalyzeService(
        ai_providers_service=ai_providers_service
    )
