from fastapi import APIRouter, Depends, status

from src.app.common.response.response_groups import (
    AI_REQUEST_TIMEOUT,
    INTERNAL_SERVER_ERROR,
    INVALID_API_KEY_OR_UNSUPPORTED_PROVIDER,
)
from src.app.ai_providers.dependencies import get_ai_providers_service
from src.app.ai_providers.schemas import (
    Provider,
    TestConnectionRequest, 
    TestConnectionResponse
)
from src.app.ai_providers.service import AIProvidersService
from src.app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/ai/providers",
    tags=["AI Providers"]
)

@router.get(
    "/",
    response_model=list[Provider],
    status_code = status.HTTP_200_OK,
    responses = {
        **INTERNAL_SERVER_ERROR
    }
)
async def get_model_providers(
    ai_providers_service: AIProvidersService = Depends(get_ai_providers_service)
) -> list[Provider]:
    """
    Get a list of supported AI providers and models.
    """
    supported_providers_models = ai_providers_service.get_supported_providers_models()

    return supported_providers_models

@router.post(
    "/test-connection",
    status_code = status.HTTP_200_OK,
    response_model = TestConnectionResponse,
    responses = {
        **INVALID_API_KEY_OR_UNSUPPORTED_PROVIDER,
        **AI_REQUEST_TIMEOUT,
        **INTERNAL_SERVER_ERROR
    }
)
async def test_provider_connection(
    test_req: TestConnectionRequest,
    ai_providers_service: AIProvidersService = Depends(get_ai_providers_service)
):
    """
    Test the connection to the AI providers.
    """
    await ai_providers_service.check_provider_connection(
        test_req.provider,
        test_req.model,
        test_req.api_key
    )

    return TestConnectionResponse(
        connection_successful=True,
        provider=test_req.provider,
        model=test_req.model
    )