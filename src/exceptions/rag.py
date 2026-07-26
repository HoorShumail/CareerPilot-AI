from src.exceptions.base import CareerPilotException

class RAGException(CareerPilotException):
    def __init__(self, message: str = "RAG retrieval failed", status_code: int = 500):
        super().__init__(message, status_code)
