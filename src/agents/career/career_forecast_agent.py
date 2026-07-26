import json
import logging
from datetime import datetime
from typing import Any, Dict

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from src.infrastructure.llm.provider import LLMProvider
from src.prompts.career_forecast_prompt import build_career_forecast_prompt
from src.schemas.career_intelligence import ForecastResponse

logger = logging.getLogger("careerpilot.career_forecast_agent")


class CareerForecastAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def generate_forecast(self, profile_payload: Dict[str, Any], context_payload: Dict[str, Any]) -> ForecastResponse:
        try:
            prompt = build_career_forecast_prompt(profile_payload, context_payload)
            response_text = await self.llm_provider.generate(prompt)
            payload = self._safe_parse_response(response_text)
            return self._validate_payload(self._normalize_payload(payload))
        except (RuntimeError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.exception("Career forecast generation hit an LLM transport failure")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI service is temporarily unavailable, please try again.",
            ) from exc

    def _safe_parse_response(self, response_text: str) -> Dict[str, Any]:
        content = response_text.strip()
        if not content:
            raise ValueError("Empty response from career forecast agent")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end < start:
                raise ValueError("Unable to parse JSON from career forecast response")
            return json.loads(content[start:end + 1])

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if "forecasts" in payload and ("generated_at" in payload or "summary" in payload):
            return payload

        forecast_payload = payload.get("forecast") if isinstance(payload.get("forecast"), dict) else None
        if forecast_payload:
            return {
                "forecasts": [forecast_payload],
                "summary": payload.get("summary") or forecast_payload.get("summary") or "",
                "generated_at": payload.get("generated_at") or datetime.utcnow(),
            }

        return payload

    def _validate_payload(self, payload: Dict[str, Any]) -> ForecastResponse:
        try:
            return ForecastResponse.model_validate(payload)
        except ValidationError as exc:
            logger.error("Career forecast response validation failed: %s", exc)
            raise ValueError("Career forecast data failed validation") from exc
