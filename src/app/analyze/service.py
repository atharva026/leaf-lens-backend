import base64
import io
from PIL import Image, UnidentifiedImageError
from fastapi import UploadFile

from langchain_core.messages import HumanMessage

from src.app.core.config import config
from src.app.core.logging import get_logger
from src.app.core.prompts.crop_analysis import CROP_ANALYSIS_PROMPT, OUTPUT_FORMAT
from src.app.core.exceptions import InvalidFileTypeException, UnsupportedProviderException
from src.app.analyze.schemas import CropHealthResponse
from src.app.ai_providers.service import AIProvidersService
from src.app.utils.ai import create_chat_model, invoke_chat_model

logger = get_logger(__name__)

# Map content-type -> PIL format name, used to cross-check actual bytes
CONTENT_TYPE_TO_PIL_FORMAT = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}

class AnalyzeService:
    def __init__(self, ai_providers_service:AIProvidersService):
        self.ai_providers_service = ai_providers_service

    def _encode_image_bytes(self, content: bytes) -> str:
        # Encode straight from bytes in memory — no disk write, no disk read.
        return base64.b64encode(content).decode("utf-8")

    def validate_image(self, content: bytes, content_type: str) -> dict:
        """
        Validate content-type, size, and that the bytes are a genuine,
        decodable image matching the declared content-type.
        """
        if not content_type or not content_type.startswith("image/"):
            return {"is_valid": False, "message": "Invalid image type"}

        if content_type not in config.ALLOWED_IMAGE_TYPES:
            return {"is_valid": False, "message": "Image type not allowed"}

        size_mb = len(content) / (1024 * 1024)
        if size_mb > config.MAX_FILE_SIZE_MB:
            return {
                "is_valid": False,
                "message": f"Image size exceeds {config.MAX_FILE_SIZE_MB} MB limit",
            }

        # Verify the bytes actually decode as an image, and that the real
        # format matches the declared content-type (catches spoofed uploads).
        try:
            image = Image.open(io.BytesIO(content))
            image.verify()  # cheap structural check
            # re-open after verify() since verify() invalidates the file pointer
            image = Image.open(io.BytesIO(content))
            actual_format = image.format
        except (UnidentifiedImageError, OSError):
            return {"is_valid": False, "message": "File is not a valid image"}

        expected_format = CONTENT_TYPE_TO_PIL_FORMAT.get(content_type)
        if expected_format and actual_format != expected_format:
            return {
                "is_valid": False,
                "message": "Image content does not match declared content type",
            }

        width, height = image.size

        # Dimension validation
        if width < config.MIN_IMAGE_DIMENSION or height < config.MIN_IMAGE_DIMENSION:
            return {
                "is_valid": False,
                "message": f"Image dimensions too small (min {config.MIN_IMAGE_DIMENSION}px)",
            }

        if width > config.MAX_IMAGE_DIMENSION_LIMIT or height > config.MAX_IMAGE_DIMENSION_LIMIT:
            return {
                "is_valid": False,
                "message": f"Image dimensions too large (max {config.MAX_IMAGE_DIMENSION_LIMIT}px)",
            }

        return {
            "is_valid": True,
            "message": "Image is valid",
            "width": width,
            "height": height,
            "size_mb": size_mb,
        }

    def resize_image_if_needed(self, content: bytes) -> bytes:
        """
        Resize the image in-memory if it exceeds the configured max dimension.
        Never touches disk.
        """
        image = Image.open(io.BytesIO(content))
        width, height = image.size

        if width <= config.MAX_IMAGE_DIMENSION and height <= config.MAX_IMAGE_DIMENSION:
            return content  # No resizing needed

        if width > height:
            new_width = config.MAX_IMAGE_DIMENSION
            new_height = int((config.MAX_IMAGE_DIMENSION / width) * height)
        else:
            new_height = config.MAX_IMAGE_DIMENSION
            new_width = int((config.MAX_IMAGE_DIMENSION / height) * width)

        resized_image = image.resize((new_width, new_height), Image.LANCZOS)
        output = io.BytesIO()
        resized_image.save(output, format=image.format)
        return output.getvalue()

    async def analyse_image(
        self,
        content: bytes,
        content_type: str,
        provider: str,
        model: str,
        api_key: str,
    ) -> dict:
        """
        Analyse image content using a user-selected LangChain chat model
        (OpenAI / Google Gemini(google_genai)) for disease detection.
        """
        # Keeping validation inside analyse_image too as protection for direct callers.
        # Validate the API key format - Basic validation
        self.ai_providers_service.validate_api_key(api_key)
        
        # Check if the provider and model are supported
        self.ai_providers_service.validate_provider_model(provider, model)

        base64_image = self._encode_image_bytes(content)

        try:
            llm = create_chat_model(provider, model, api_key)
            structured_llm = llm.with_structured_output(CropHealthResponse)
        except UnsupportedProviderException:
            raise
        except Exception as error:
            logger.error("Failed to configure structured chat model %s:%s - %s", provider, model, error)
            raise UnsupportedProviderException(
                message=f"Could not initialize model '{model}' for provider '{provider}'"
            )

        message = HumanMessage(
            content=[
                {"type": "text", "text": CROP_ANALYSIS_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{content_type};base64,{base64_image}"},
                },
            ]
        )

        response = await invoke_chat_model(structured_llm, [message])

        return response

    async def process_single_image(
        self,
        file: UploadFile,
        provider: str,
        model: str,
        api_key: str,
    ) -> dict:
        """Validate, resize, and analyse one uploaded image in memory."""
        # Validate the API key format - Basic validation
        self.ai_providers_service.validate_api_key(api_key)
                
        # Check if the provider and model are supported
        self.ai_providers_service.validate_provider_model(provider, model)

        content = await file.read()

        validation = self.validate_image(content, file.content_type)
        if not validation["is_valid"]:
            raise InvalidFileTypeException(message=validation["message"])

        processed = self.resize_image_if_needed(content)
        return await self.analyse_image(
            processed,
            file.content_type,
            provider,
            model,
            api_key,
        )