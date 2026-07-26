from typing import Dict, Any
from src.infrastructure.document_parser.resume_parser import ResumeParser

class ResumeParserAgent:
    def __init__(self):
        self.parser = ResumeParser()

    def parse(self, file_bytes: bytes, content_type: str) -> Dict[str, Any]:
        return self.parser.parse_resume(file_bytes, content_type)
