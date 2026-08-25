from src.app.common.response.build_example import build_example

# 400 Bad Request
INVALID_FILE_TYPE_EXAMPLE = {
    "InvalidFileType": build_example(
        summary="Invalid file type",
        code="INVALID_FILE_TYPE",
        message="Invalid file type. Please upload an image.",
    )
}

INVALID_IMAGE_EXAMPLE = {
    "InvalidImage": build_example(
        summary="Invalid image",
        code="INVALID_IMAGE",
        message="Invalid image. Please upload a valid image.",
    )
}

INVALID_API_KEY_EXAMPLE = {
    "InvalidAPIKey": build_example(
        summary="Invalid API key",
        code="INVALID_API_KEY",
        message="Invalid API key",
    )
}

UNSUPPORTED_PROVIDER_EXAMPLE = {
    "UnsupportedProvider": build_example(
        summary="Unsupported provider or model",
        code="UNSUPPORTED_PROVIDER",
        message="Unsupported provider or model",
    )
}

# 408 Request Timeout
AI_REQUEST_TIMEOUT_EXAMPLE = {
    "AIRequestTimeout": build_example(
        summary="AI request timed out",
        code="AI_REQUEST_TIMEOUT",
        message="AI request timed out",
    )
}

# 429
TOO_MANY_REQUESTS_EXAMPLE = {
    "TooManyRequests": build_example(
        summary="Too many requests",
        code="TOO_MANY_REQUESTS",
        message="Too many requests. Please try again later.",
    )
}

# 500
INTERNAL_SERVER_ERROR_EXAMPLE = {
    "InternalServerError": build_example(
        summary="Internal server error",
        code="INTERNAL_SERVER_ERROR",
        message="Something went wrong",
    )
}
