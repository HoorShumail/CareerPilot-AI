from src.exceptions.base import CareerPilotException

class ResumeParseException(CareerPilotException):
    def __init__(self, message: str = "Failed to parse resume", status_code: int = 400):
        super().__init__(message, status_code)
