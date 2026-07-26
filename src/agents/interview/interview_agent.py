import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from src.infrastructure.llm.provider import LLMProvider
from src.prompts.evaluation_prompt import build_evaluation_prompt
from src.prompts.followup_prompt import build_followup_prompt
from src.prompts.interview_prompt import build_interview_prompt
from src.prompts.interview_final_feedback_prompt import (  # <-- CHANGED
    build_interview_final_feedback_prompt,
)
from src.schemas.interview import InterviewSessionResponse

logger = logging.getLogger("careerpilot.interview_agent")


class InterviewAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def generate_session(
        self,
        profile_payload: Dict[str, Any],
        context_payload: Dict[str, Any],
        request_payload: Any,
    ) -> InterviewSessionResponse:
        try:
            prompt = build_interview_prompt(profile_payload, context_payload)
            response_text = await self.llm_provider.generate(prompt)
            payload = self._safe_parse_response(response_text)
            normalized = self._normalize_session_payload(payload, request_payload)
            return self._validate_payload(normalized)
        except (RuntimeError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.exception("Interview session generation hit an LLM transport failure")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI service is temporarily unavailable, please try again.",
            ) from exc

    async def evaluate_answer(self, question: str, answer: str) -> Dict[str, Any]:
        try:
            prompt = build_evaluation_prompt(question, answer)
            response_text = await self.llm_provider.generate(prompt)
            payload = self._safe_parse_response(response_text)
            return self._normalize_evaluation(payload)
        except (RuntimeError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.exception("Interview answer evaluation hit an LLM transport failure")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI service is temporarily unavailable, please try again.",
            ) from exc

    async def generate_follow_up(self, question: str, answer: str) -> Dict[str, Any]:
        try:
            prompt = build_followup_prompt(question, answer)
            response_text = await self.llm_provider.generate(prompt)
            payload = self._safe_parse_response(response_text)
            return self._normalize_followup(payload)
        except (RuntimeError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.exception("Interview follow-up generation hit an LLM transport failure")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI service is temporarily unavailable, please try again.",
            ) from exc

    # -------- CHANGED: uses the new final feedback prompt --------
    async def generate_feedback(self, session_payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            prompt = build_interview_final_feedback_prompt(session_payload)
            response_text = await self.llm_provider.generate(prompt)
            payload = self._safe_parse_response(response_text)
            return self._normalize_feedback(payload)
        except (RuntimeError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.exception("Interview feedback generation hit an LLM transport failure")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI service is temporarily unavailable, please try again.",
            ) from exc

    # -------- Helpers --------
    def _safe_parse_response(self, response_text: str) -> Dict[str, Any]:
        content = response_text.strip()
        if not content:
            raise ValueError("Empty response from interview agent")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end < start:
                raise ValueError("Unable to parse JSON from interview response")
            return json.loads(content[start:end + 1])

    def _normalize_session_payload(
        self,
        payload: Dict[str, Any],
        request_payload: Any,
    ) -> Dict[str, Any]:
        questions = payload.get("questions") or []
        if not isinstance(questions, list):
            questions = []
        return {
            "id": payload.get("id") or str(uuid.uuid4()),
            "user_id": payload.get("user_id") or str(uuid.uuid4()),
            "interview_type": payload.get("interview_type") or getattr(request_payload, "interview_type", None),
            "target_role": payload.get("target_role") or getattr(request_payload, "target_role", None),
            "target_company": payload.get("target_company") or getattr(request_payload, "target_company", None),
            "difficulty": payload.get("difficulty") or getattr(request_payload, "difficulty", None),
            "duration_seconds": payload.get("duration_seconds") or getattr(request_payload, "duration_seconds", None),
            "questions": questions,
            "overall_score": payload.get("overall_score"),
            "feedback_summary": payload.get("feedback") or {},
            "created_at": payload.get("created_at") or datetime.utcnow(),
            "updated_at": payload.get("updated_at") or datetime.utcnow(),
        }

    def _normalize_evaluation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "technical_score": payload.get("technical_score"),
            "communication_score": payload.get("communication_score"),
            "confidence_score": payload.get("confidence_score"),
            "completeness": payload.get("completeness"),
            "correctness": payload.get("correctness"),
            "improvement_suggestions": payload.get("improvement_suggestions") or [],
            "follow_up_question": payload.get("follow_up_question") or "",
        }

    def _normalize_followup(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "follow_up_question": payload.get("follow_up_question") or "",
            "category": payload.get("category") or "technical",
        }

    # -------- CHANGED: stores all new fields --------
    def _normalize_feedback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "overall_score": payload.get("overall_score", 0),
            "technical_score": payload.get("technical_score", 0),
            "communication_score": payload.get("communication_score", 0),
            "confidence_score": payload.get("confidence_score", 0),
            "strengths": payload.get("strengths", []),
            "weaknesses": payload.get("weaknesses", []),
            "missing_concepts": payload.get("missing_concepts", []),
            "recommended_learning": payload.get("recommended_learning", []),
            "hire_recommendation": payload.get("hire_recommendation", ""),
            "summary": payload.get("summary", ""),
            "next_steps": payload.get("next_steps", []),
        }

    def _validate_payload(self, payload: Dict[str, Any]) -> InterviewSessionResponse:
        try:
            return InterviewSessionResponse.model_validate(payload)
        except ValidationError as exc:
            logger.error("Interview session response validation failed: %s", exc)
            raise ValueError("Interview session data failed validation") from exc