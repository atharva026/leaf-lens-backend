from fastapi import APIRouter

from src.app.common.response.response_groups import TOO_MANY_REQUESTS
from src.app.analyze.routes import router as analyze_router
from src.app.ai_providers.routes import router as ai_provider_router

api_router = APIRouter(
    # Set Too Many Requests response for all endpoints in this router by default.
    responses={
        **TOO_MANY_REQUESTS,
    }
)

# Include routers
api_router.include_router(analyze_router)
api_router.include_router(ai_provider_router)
