from fastapi import status

class AppException(Exception):
    """Base application exception"""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR  # default

    def __init__(self, message: str, code: str = "APP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)

class UnauthorizedException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, code="UNAUTHORIZED")

class ForbiddenException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, code="FORBIDDEN")

class ValidationException(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, code="VALIDATION_ERROR")

class UnexpectedException(AppException):
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    def __init__(self, message: str = "Something went wrong"):
        super().__init__(message, code="INTERNAL_SERVER_ERROR")
        
# ----------------------------------------------------------------------

class InvalidFileTypeException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    def __init__(self, message: str = "Invalid file type. Please upload an image."):
        super().__init__(message, code="INVALID_FILE_TYPE")

class InvalidImageException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    def __init__(self, message: str = "Invalid image. Please upload a valid image."):
        super().__init__(message, code="INVALID_IMAGE")

class InvalidAPIKeyException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    def __init__(self, message: str = "Invalid API key"):
        super().__init__(message, code="INVALID_API_KEY")

class UnsupportedProviderException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    def __init__(self, message: str = "Unsupported provider or model"):
        super().__init__(message, code="UNSUPPORTED_PROVIDER")
        
class AIRequestTimeoutException(AppException):
    status_code = status.HTTP_408_REQUEST_TIMEOUT
    def __init__(self, message: str = "AI request timed out"):
        super().__init__(message, code="AI_REQUEST_TIMEOUT")

