from typing import Dict, List, Optional
from pydantic import BaseModel
from src.utils.normalization import normalize_payload_for_model, normalize_value_for_annotation


class SampleSchema(BaseModel):
    title: str
    skills: List[str]
    metadata: Dict[str, bool]
    summary: Optional[str] = None


def test_normalize_dict_to_string():
    res = normalize_value_for_annotation({"key": "val"}, str)
    assert res == '{"key": "val"}'


def test_normalize_list_to_comma_string():
    res = normalize_value_for_annotation(["Python", "FastAPI"], str)
    assert res == "Python, FastAPI"


def test_normalize_none_to_empty_string():
    res = normalize_value_for_annotation(None, str)
    assert res == ""


def test_normalize_string_to_list():
    res = normalize_value_for_annotation("Docker, Kubernetes", List[str])
    assert res == ["Docker", "Kubernetes"]


def test_normalize_list_to_dict():
    res = normalize_value_for_annotation(["AWS", "GCP"], Dict[str, bool])
    assert res == {"AWS": True, "GCP": True}


def test_normalize_payload_for_model():
    payload = {
        "title": ["Senior", "DevOps"],
        "skills": "Python, Docker",
        "metadata": ["AWS"],
        "summary": None,
    }
    normalized = normalize_payload_for_model(payload, SampleSchema)
    validated = SampleSchema.model_validate(normalized)

    assert validated.title == "Senior, DevOps"
    assert validated.skills == ["Python", "Docker"]
    assert validated.metadata == {"AWS": True}
    assert validated.summary == ""
