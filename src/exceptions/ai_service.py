"""AI service exception hierarchy for CareerPilot-AI."""

from src.exceptions.base import CareerPilotException


class AIServiceException(CareerPilotException):
    """Base exception for all AI/LLM service failures."""

    def __init__(self, message: str = "AI service error", status_code: int = 500):
        super().__init__(message, status_code)


class AIResponseParsingException(AIServiceException):
    """Raised when the AI response cannot be parsed as valid JSON after all repair attempts."""

    def __init__(self, message: str = "AI response could not be parsed as valid JSON"):
        super().__init__(message, 500)


class AIResponseTruncatedException(AIServiceException):
    """Raised when the AI response was truncated due to token limits and could not be recovered."""

    def __init__(self, message: str = "AI response was truncated due to token limits"):
        super().__init__(message, 500)


class AIResponseValidationException(AIServiceException):
    """Raised when the parsed AI response fails Pydantic schema validation."""

    def __init__(self, message: str = "AI response failed schema validation"):
        super().__init__(message, 500)
