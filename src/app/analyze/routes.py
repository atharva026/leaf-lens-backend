from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from src.app.analyze.dependencies import get_analyze_service
from src.app.analyze.service import AnalyzeService
from src.app.analyze.schemas import AnalyzeImageResponse
from src.app.common.response.response_groups import (
    INVALID_REQUEST_OR_UNSUPPORTED_PROVIDER,
    AI_REQUEST_TIMEOUT,
    INTERNAL_SERVER_ERROR
)
router = APIRouter(
    prefix="/analyze",
    tags=["Analyze"]
)

@router.post(
    "/",
    response_model = AnalyzeImageResponse,
    status_code = status.HTTP_200_OK,
    responses = {
        **INVALID_REQUEST_OR_UNSUPPORTED_PROVIDER,
        **AI_REQUEST_TIMEOUT,
        **INTERNAL_SERVER_ERROR
    }
)
async def analyse_image(
    file: UploadFile = File(..., description="Image file to be analyzed"),
    provider: str = Form(..., description="AI Provider e.g. OpenAI / Google Gemini(google_genai)"),
    model: str = Form(..., description="model e.g. gpt-5.5, gemini-3.5, qwen"),
    api_key: str = Form(..., description="AI Provider API key"),
    analyze_service: AnalyzeService = Depends(get_analyze_service)
):
    """
    Endpoint to upload an image for disease detection.
    Caller supplies provider:model (form field) and their own API key (header).
    """
    result = await analyze_service.process_single_image(
        file,
        provider,
        model,
        api_key
    )

    return AnalyzeImageResponse(
        file_name=file.filename,
        content_type=file.content_type,
        provider=provider,
        model=model,
        result=result
    )
