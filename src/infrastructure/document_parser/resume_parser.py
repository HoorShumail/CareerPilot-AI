import io
import re
from pathlib import Path
from typing import Dict, Optional

from src.exceptions.resume import ResumeParseException


def _import_docx():
    try:
        import docx
    except ImportError as exc:
        raise ResumeParseException("The python-docx library is required to parse Word resumes") from exc
    return docx


def _import_fitz():
    try:
        import fitz
    except ImportError as exc:
        raise ResumeParseException("The pymupdf library is required to parse PDF resumes") from exc
    return fitz


def _import_pdf2image():
    try:
        from pdf2image import convert_from_bytes
    except ImportError as exc:
        raise ResumeParseException("The pdf2image library is required for OCR fallback") from exc
    return convert_from_bytes


def _import_pytesseract():
    try:
        import pytesseract
    except ImportError as exc:
        raise ResumeParseException("The pytesseract library is required for OCR fallback") from exc
    return pytesseract

SUPPORTED_FILE_TYPES = {"pdf", "docx"}

class ResumeParser:
    def __init__(self):
        pass

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        fitz = _import_fitz()
        try:
            text = ""
            with fitz.open(stream=file_bytes, filetype="pdf") as document:
                for page in document:
                    text += page.get_text()
            if text and text.strip():
                return text
            return self.extract_text_with_ocr(file_bytes)
        except Exception:
            return self.extract_text_with_ocr(file_bytes)

    def extract_text_from_docx(self, file_bytes: bytes) -> str:
        docx = _import_docx()
        try:
            document = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
            return text
        except Exception as exc:
            raise ResumeParseException(str(exc))

    def extract_text_with_ocr(self, file_bytes: bytes) -> str:
        convert_from_bytes = _import_pdf2image()
        pytesseract = _import_pytesseract()
        try:
            images = convert_from_bytes(file_bytes)
            text = "\n".join(pytesseract.image_to_string(image) for image in images)
            return text
        except Exception as exc:
            raise ResumeParseException(str(exc))

    def parse_resume_text(self, text: str) -> Dict[str, Optional[str]]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        skills = self._extract_skills(lines)
        experience = self._extract_section(text, ["experience", "work experience", "professional experience"])
        education = self._extract_section(text, ["education", "academic background", "education & training"])
        summary = self._extract_section(text, ["summary", "professional summary", "profile"])
        return {
            "full_name": lines[0] if lines else None,
            "email": email,
            "phone": phone,
            "summary": summary,
            "skills": skills,
            "experience": experience,
            "education": education,
        }

    def parse_resume(self, file_bytes: bytes, content_type: str) -> Dict[str, Optional[str]]:
        content_type = content_type.lower()
        if content_type == "application/pdf":
            text = self.extract_text_from_pdf(file_bytes)
        elif content_type in {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"}:
            try:
                text = self.extract_text_from_docx(file_bytes)
            except ResumeParseException:
                text = self.extract_text_with_ocr(file_bytes)
        else:
            raise ResumeParseException("Unsupported resume file type")
        return self.parse_resume_text(text)

    def _extract_email(self, text: str) -> Optional[str]:
        match = re.search(r"[\w\.-]+@[\w\.-]+", text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        match = re.search(r"\+?\d[\d\s\-()]{7,}\d", text)
        return match.group(0) if match else None

    def _extract_skills(self, lines: list[str]) -> Optional[str]:
        skills = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ["skills", "technical skills", "competencies"]):
                skills.append(line)
        return "; ".join(skills) if skills else None

    def _extract_section(self, text: str, headings: list[str]) -> Optional[str]:
        lowered = text.lower()
        for heading in headings:
            if heading in lowered:
                start = lowered.index(heading)
                snippet = text[start: start + 2000]
                return snippet.strip()
        return None
