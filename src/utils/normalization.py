import json
import logging
from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin

from pydantic import BaseModel

logger = logging.getLogger("careerpilot.normalization")


def normalize_string(value: Any) -> str:
    """
    Safely coerces any value to a string according to normalization rules:
      - None -> ""
      - dict ({}) -> "" (or extracted text content/JSON if non-empty)
      - list -> comma-separated string
      - int/float/bool -> str(value)
      - string -> keep unchanged
    """
    if value is None:
        return ""
    if isinstance(value, dict):
        if not value:
            return ""
        for key in ["summary", "details", "analysis", "notes", "recommendation", "gap"]:
            if key in value and isinstance(value[key], str):
                return value[key]
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item is not None)
    if isinstance(value, (int, float, bool)):
        return str(value)
    return str(value)


def normalize_value_for_annotation(value: Any, annotation: Any) -> Any:
    """
    Safely coerces a single value to match an expected type annotation (Pydantic v2).
    Supported target conversions:
      - dict -> string (JSON serialization / text extraction or "" if empty)
      - list -> comma-separated string (or single item str)
      - None -> empty string / empty list / empty dict
      - string -> list of strings
      - list -> dict (mapping items to True)
    """
    origin = get_origin(annotation)
    args = get_args(annotation)

    # Unwrap Optional / Union types (e.g., Optional[str] -> str)
    if origin is Union:
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            annotation = non_none_args[0]
            origin = get_origin(annotation)
            args = get_args(annotation)

    # 1. Target is str
    if annotation is str:
        return normalize_string(value)

    # 2. Target is list / List[...]
    if annotation is list or origin is list or origin is List:
        if value is None:
            return []
        if isinstance(value, str):
            value_str = value.strip()
            if not value_str:
                return []
            if "," in value_str:
                return [item.strip() for item in value_str.split(",") if item.strip()]
            return [value_str]
        if isinstance(value, dict):
            return [value]
        if isinstance(value, list):
            item_type = args[0] if args else Any
            return [normalize_value_for_annotation(item, item_type) for item in value]

    # 3. Target is dict / Dict[...]
    if annotation is dict or origin is dict or origin is Dict:
        if value is None:
            return {}
        if isinstance(value, list):
            return {str(item): True for item in value if item is not None}
        if isinstance(value, str):
            val_str = value.strip()
            if not val_str:
                return {}
            try:
                parsed = json.loads(val_str)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
            return {val_str: True}
        if isinstance(value, dict):
            return value

    # 4. Target is Pydantic BaseModel class
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        if isinstance(value, dict):
            return normalize_payload_for_model(value, annotation)

    # Return value unchanged if no matching conversion is needed
    return value


def normalize_payload_for_model(payload: Dict[str, Any], model_cls: Type[BaseModel]) -> Dict[str, Any]:
    """
    Safely normalizes dictionary payload keys against a Pydantic model's field annotations
    before calling model_validate.
    """
    if not isinstance(payload, dict):
        return payload

    normalized = dict(payload)
    if not hasattr(model_cls, "model_fields"):
        return normalized

    for field_name, field_info in model_cls.model_fields.items():
        if field_name in normalized:
            raw_val = normalized[field_name]
            annotation = field_info.annotation
            normalized[field_name] = normalize_value_for_annotation(raw_val, annotation)

    return normalized
