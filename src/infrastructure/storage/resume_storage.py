from pathlib import Path
from uuid import uuid4
from typing import BinaryIO

from src.config.settings import settings

class ResumeStorage:
    def __init__(self):
        self.base_dir = Path(settings.RESUME_STORAGE_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_resume_file(self, filename: str, content: bytes) -> str:
        safe_name = Path(filename).name
        unique_name = f"{uuid4().hex}_{safe_name}"
        path = self.base_dir / unique_name
        with open(path, "wb") as f:
            f.write(content)
        return str(path)

    def get_resume_file_path(self, filename: str) -> str:
        path = self.base_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Resume file not found: {filename}")
        return str(path)

    def list_resume_files(self) -> list[str]:
        return [str(p) for p in self.base_dir.glob("**/*") if p.is_file()]
