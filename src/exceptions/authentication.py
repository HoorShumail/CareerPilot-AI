from src.exceptions.base import CareerPilotException

class AuthenticationException(CareerPilotException):
    def __init__(self, message: str = "Authentication failed", status_code: int = 401):
        super().__init__(message, status_code)

class UserNotFoundException(CareerPilotException):
    def __init__(self, message: str = "User not found", status_code: int = 404):
        super().__init__(message, status_code)
