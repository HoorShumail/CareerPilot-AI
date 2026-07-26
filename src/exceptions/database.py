from src.exceptions.base import CareerPilotException

class DatabaseException(CareerPilotException):
    def __init__(self, message: str = "Database error occurred", status_code: int = 500):
        super().__init__(message, status_code)
