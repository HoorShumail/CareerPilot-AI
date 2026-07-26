import json
import logging
from datetime import datetime
from typing import Any, Dict

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from src.infrastructure.llm.provider import LLMProvider
from src.prompts.market_intelligence_prompt import build_market_intelligence_prompt
from src.schemas.career_intelligence import MarketIntelligenceResponse

logger = logging.getLogger("careerpilot.market_intelligence_agent")


class MarketIntelligenceAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def generate_market_intelligence(self, profile_payload: Dict[str, Any], context_payload: Dict[str, Any]) -> MarketIntelligenceResponse:
        try:
            prompt = build_market_intelligence_prompt(profile_payload, context_payload)
            response_text = await self.llm_provider.generate(prompt)
            payload = self._safe_parse_response(response_text)
            return self._validate_payload(self._normalize_payload(payload))
        except (RuntimeError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.exception("Market intelligence generation hit an LLM transport failure")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI service is temporarily unavailable, please try again.",
            ) from exc

    def _safe_parse_response(self, response_text: str) -> Dict[str, Any]:
        content = response_text.strip()
        if not content:
            raise ValueError("Empty response from market intelligence agent")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end < start:
                raise ValueError("Unable to parse JSON from market intelligence response")
            return json.loads(content[start:end + 1])

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        market_payload = payload.get("market_summary") if isinstance(payload.get("market_summary"), dict) else None
        if market_payload:
            return {
                "demanded_skills": market_payload.get("demanded_skills") or payload.get("demanded_skills") or [],
                "technologies": market_payload.get("technologies") or payload.get("technologies") or [],
                "certifications": market_payload.get("certifications") or payload.get("certifications") or [],
                "frameworks": market_payload.get("frameworks") or payload.get("frameworks") or [],
                "ai_tools": market_payload.get("ai_tools") or payload.get("ai_tools") or [],
                "cloud_providers": market_payload.get("cloud_providers") or payload.get("cloud_providers") or [],
                "programming_languages": market_payload.get("programming_languages") or payload.get("programming_languages") or [],
                "trends": market_payload.get("trends") or payload.get("trends") or [],
                "generated_at": market_payload.get("generated_at") or payload.get("generated_at") or datetime.utcnow(),
            }
        return payload

    def _validate_payload(self, payload: Dict[str, Any]) -> MarketIntelligenceResponse:
        try:
            return MarketIntelligenceResponse.model_validate(payload)
        except ValidationError as exc:
            logger.error("Market intelligence response validation failed: %s", exc)
            raise ValueError("Market intelligence data failed validation") from exc
