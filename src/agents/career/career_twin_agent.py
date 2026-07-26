import json
import logging
from typing import Any, Dict

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from src.infrastructure.llm.provider import LLMProvider
from src.prompts.career_twin_prompt import build_career_twin_prompt
from src.schemas.career_profile import CareerProfileCreate

logger = logging.getLogger("careerpilot.career_twin_agent")


class CareerTwinAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def refresh_profile(self, profile_payload: Dict[str, Any], context_payload: Dict[str, Any]) -> CareerProfileCreate:
        try:
            prompt = build_career_twin_prompt(profile_payload, context_payload)
            response_text = await self.llm_provider.generate(prompt)
            payload = self._safe_parse_response(response_text)
            return self._validate_payload(payload)
        except (RuntimeError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.exception("Career twin refresh hit an LLM transport failure")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI service is temporarily unavailable, please try again.",
            ) from exc

    def _safe_parse_response(self, response_text: str) -> Dict[str, Any]:
        content = response_text.strip()
        if not content:
            raise ValueError("Empty response from career twin agent")

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end < start:
                raise ValueError("Unable to parse JSON from career twin response") from None
            return json.loads(content[start : end + 1])

    def _validate_payload(self, payload: Dict[str, Any]) -> CareerProfileCreate:
        try:
            return CareerProfileCreate.model_validate(payload)
        except ValidationError as exc:
            logger.error("Career twin response validation failed: %s", exc)
            raise ValueError("Career twin data failed validation") from exc
