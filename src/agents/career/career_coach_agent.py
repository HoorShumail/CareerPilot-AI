import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from src.infrastructure.llm.provider import LLMProvider
from src.prompts.career_coach_prompt import build_career_coach_prompt
from src.schemas.career_intelligence import CoachChatResponse

logger = logging.getLogger("careerpilot.career_coach_agent")


class CareerCoachAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def generate_chat_response(
        self,
        profile_payload: Dict[str, Any],
        context_payload: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> CoachChatResponse:
        try:
            prompt = build_career_coach_prompt(profile_payload, context_payload, conversation_history)
            response_text = await self.llm_provider.generate(prompt)
            payload = self._safe_parse_response(response_text)
            return self._validate_payload(self._normalize_payload(payload))
        except (RuntimeError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.exception("Career coach generation hit an LLM transport failure")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI service is temporarily unavailable, please try again.",
            ) from exc

    def _safe_parse_response(self, response_text: str) -> Dict[str, Any]:
        content = response_text.strip()
        if not content:
            raise ValueError("Empty response from career coach agent")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end < start:
                raise ValueError("Unable to parse JSON from career coach response")
            return json.loads(content[start:end + 1])

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        coach_payload = payload.get("coach_response") if isinstance(payload.get("coach_response"), dict) else None
        if coach_payload:
            return {
                "message": coach_payload.get("message") or payload.get("message") or "",
                "action_items": coach_payload.get("action_items") or payload.get("action_items") or [],
                "confidence": coach_payload.get("confidence") or payload.get("confidence") or 0.0,
                "conversation_id": coach_payload.get("conversation_id") or payload.get("conversation_id"),
                "generated_at": coach_payload.get("generated_at") or payload.get("generated_at") or datetime.utcnow(),
            }
        return payload

    def _validate_payload(self, payload: Dict[str, Any]) -> CoachChatResponse:
        try:
            return CoachChatResponse.model_validate(payload)
        except ValidationError as exc:
            logger.error("Career coach response validation failed: %s", exc)
            raise ValueError("Career coach data failed validation") from exc
