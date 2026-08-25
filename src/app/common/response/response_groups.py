from fastapi import status
from src.app.common.response import examples
from src.app.common.response.response_builder import ResponseBuilder

# 400
INVALID_REQUEST_OR_UNSUPPORTED_PROVIDER = ResponseBuilder.build(
    status.HTTP_400_BAD_REQUEST,
    examples.INVALID_FILE_TYPE_EXAMPLE,
    examples.INVALID_IMAGE_EXAMPLE,
    examples.INVALID_API_KEY_EXAMPLE,
    examples.UNSUPPORTED_PROVIDER_EXAMPLE
)

INVALID_API_KEY_OR_UNSUPPORTED_PROVIDER = ResponseBuilder.build(
    status.HTTP_400_BAD_REQUEST,
    examples.INVALID_API_KEY_EXAMPLE,
    examples.UNSUPPORTED_PROVIDER_EXAMPLE
)

# 408
AI_REQUEST_TIMEOUT = ResponseBuilder.build(
    status.HTTP_408_REQUEST_TIMEOUT,
    examples.AI_REQUEST_TIMEOUT_EXAMPLE
)

# 429
TOO_MANY_REQUESTS = ResponseBuilder.build(
    status.HTTP_429_TOO_MANY_REQUESTS,
    examples.TOO_MANY_REQUESTS_EXAMPLE
)

# 500
INTERNAL_SERVER_ERROR = ResponseBuilder.build(
    status.HTTP_500_INTERNAL_SERVER_ERROR,
    examples.INTERNAL_SERVER_ERROR_EXAMPLE
)