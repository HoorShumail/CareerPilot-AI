import json
import logging
from typing import Any, Dict

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from src.infrastructure.llm.provider import LLMProvider
from src.prompts.job_prompts import build_job_insights_prompt
from src.schemas.job import JobInsights
from src.utils.normalization import normalize_payload_for_model

logger = logging.getLogger("careerpilot.job_insights_agent")


class JobInsightsAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def generate_insights(self, parsed_job: Dict[str, Any]) -> JobInsights:
        try:
            prompt = build_job_insights_prompt(parsed_job)
            response_text = await self.llm_provider.generate(prompt)

            parsed_payload = self._safe_parse_response(response_text)
            normalized_payload = self._normalize_insights_payload(parsed_payload)

            return self._validate_insights(normalized_payload)
        except (RuntimeError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.exception("Job insights generation hit an LLM transport failure")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI service is temporarily unavailable, please try again.",
            ) from exc

    def _safe_parse_response(self, response_text: str) -> Dict[str, Any]:
        content = response_text.strip()

        if not content:
            logger.error("Job insights agent received empty response")
            raise ValueError("Empty response from job insights agent")

        for attempt in range(2):
            try:
                return json.loads(content)
            except json.JSONDecodeError as exc:
                logger.warning(
                    "Job insights JSON decode failed on attempt %s: %s",
                    attempt + 1,
                    exc,
                )
                content = self._extract_json_snippet(content)

        logger.error("Job insights failed to parse JSON after retries: %s", response_text)
        raise ValueError("Unable to parse JSON from job insights response")

    def _extract_json_snippet(self, raw_text: str) -> str:
        start = raw_text.find("{")
        end = raw_text.rfind("}")

        if start == -1 or end == -1 or end < start:
            return raw_text

        return raw_text[start:end + 1]

    def _normalize_insights_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert every list returned by the LLM into a JSON object.

        Example:
            ["Python", "FastAPI"]

        becomes

            {
                "Python": True,
                "FastAPI": True
            }

        This matches the JobInsights schema, where these fields are Dict[str, Any].
        """

        normalized = payload.copy()

        for key, value in normalized.items():

            if isinstance(value, list):

                normalized[key] = {
                    str(item): True
                    for item in value
                }

            elif value is None:

                normalized[key] = {}

        return normalized

    def _validate_insights(self, payload: Dict[str, Any]) -> JobInsights:
        try:
            normalized_payload = normalize_payload_for_model(payload, JobInsights)
            return JobInsights.model_validate(normalized_payload)

        except ValidationError as exc:

            logger.error("Job insights validation failed.")
            logger.error("Payload received:")
            logger.error(json.dumps(payload, indent=2, default=str))
            logger.exception(exc)

            raise ValueError("Job insights data failed validation") from exc