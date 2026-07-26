import json
import logging
from datetime import datetime
from typing import Any, Dict

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from src.infrastructure.llm.provider import LLMProvider
from src.prompts.learning_planner_prompt import build_learning_planner_prompt
from src.schemas.career_intelligence import LearningPlanResponse

logger = logging.getLogger("careerpilot.learning_planner_agent")


class LearningPlannerAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def generate_learning_plan(self, profile_payload: Dict[str, Any], context_payload: Dict[str, Any]) -> LearningPlanResponse:
        try:
            prompt = build_learning_planner_prompt(profile_payload, context_payload)
            response_text = await self.llm_provider.generate(prompt)
            payload = self._safe_parse_response(response_text)
            return self._validate_payload(self._normalize_payload(payload))
        except (RuntimeError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.exception("Learning planner generation hit an LLM transport failure")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI service is temporarily unavailable, please try again.",
            ) from exc

    def _safe_parse_response(self, response_text: str) -> Dict[str, Any]:
        content = response_text.strip()
        if not content:
            raise ValueError("Empty response from learning planner agent")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end < start:
                raise ValueError("Unable to parse JSON from learning planner response")
            return json.loads(content[start:end + 1])

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        plan_payload = payload.get("learning_plan") if isinstance(payload.get("learning_plan"), dict) else None
        if plan_payload:
            return {
                "daily": plan_payload.get("daily") or payload.get("daily") or [],
                "weekly": plan_payload.get("weekly") or payload.get("weekly") or [],
                "monthly": plan_payload.get("monthly") or payload.get("monthly") or [],
                "quarterly": plan_payload.get("quarterly") or payload.get("quarterly") or [],
                "yearly": plan_payload.get("yearly") or payload.get("yearly") or [],
                "books": plan_payload.get("books") or payload.get("books") or [],
                "projects": plan_payload.get("projects") or payload.get("projects") or [],
                "certifications": plan_payload.get("certifications") or payload.get("certifications") or [],
                "courses": plan_payload.get("courses") or payload.get("courses") or [],
                "research_papers": plan_payload.get("research_papers") or payload.get("research_papers") or [],
                "open_source_contributions": plan_payload.get("open_source_contributions") or payload.get("open_source_contributions") or [],
                "generated_at": plan_payload.get("generated_at") or payload.get("generated_at") or datetime.utcnow(),
            }
        return payload

    def _validate_payload(self, payload: Dict[str, Any]) -> LearningPlanResponse:
        try:
            return LearningPlanResponse.model_validate(payload)
        except ValidationError as exc:
            logger.error("Learning plan response validation failed: %s", exc)
            raise ValueError("Learning plan data failed validation") from exc
