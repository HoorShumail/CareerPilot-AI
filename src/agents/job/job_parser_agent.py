import json
import logging
from typing import Any, Dict

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from src.infrastructure.llm.provider import LLMProvider
from src.prompts.job_prompts import build_job_parsing_prompt
from src.schemas.job import JobParsedData
from src.utils.normalization import normalize_payload_for_model


logger = logging.getLogger("careerpilot.job_parser_agent")


class JobParserAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def parse(self, raw_description: str) -> JobParsedData:
        try:
            prompt = build_job_parsing_prompt(raw_description)
            response_text = await self.llm_provider.generate(prompt)

            parsed_payload = self._safe_parse_response(response_text)
            normalized_payload = self._normalize_payload(parsed_payload)

            print("\n==============================")
            print("RAW LLM RESPONSE")
            print(response_text)
            print("==============================")

            print("\n==============================")
            print("NORMALIZED PAYLOAD")
            print(normalized_payload)
            print("==============================")

            return self._validate_payload(normalized_payload)
        except (RuntimeError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.exception("Job parser hit an LLM transport failure")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI service is temporarily unavailable, please try again.",
            ) from exc


    def _safe_parse_response(self, response_text: str) -> Dict[str, Any]:
        content = response_text.strip()

        if not content:
            raise ValueError("Empty response from Job Parser")

        for _ in range(2):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                content = self._extract_json(content)

        raise ValueError("Unable to parse JSON from Job Parser")

    def _extract_json(self, text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            return text

        return text[start:end + 1]

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized = payload.copy()

        list_fields = [
            "responsibilities",
            "required_skills",
            "preferred_skills",
            "education",
            "certifications",
            "technologies",
            "soft_skills",
            "keywords",
        ]

        for field in list_fields:
            value = normalized.get(field)

            if value is None:
                normalized[field] = []
            elif isinstance(value, str):
                normalized[field] = [value]
            elif not isinstance(value, list):
                normalized[field] = [str(value)]

        return normalized

    def _validate_payload(self, payload: Dict[str, Any]) -> JobParsedData:
        try:
            normalized_payload = normalize_payload_for_model(payload, JobParsedData)
            return JobParsedData.model_validate(normalized_payload)
        except ValidationError as exc:

            logger.exception("Job parser validation failed")
            raise ValueError("Parsed job data failed validation") from exc