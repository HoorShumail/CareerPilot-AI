import json
import logging
from typing import Any, Dict

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from src.infrastructure.llm.provider import LLMProvider
from src.prompts.job_match_prompt import build_job_match_prompt
from src.prompts.job_prompts import build_job_match_prompt as build_legacy_job_match_prompt
from src.schemas.application import MatchAnalysis
from src.schemas.match import MatchComparisonResponse
from src.utils.normalization import normalize_payload_for_model, normalize_string

logger = logging.getLogger("careerpilot.job_matcher_agent")


class JobMatcherAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def compare(self, resume_version: Dict[str, Any], job_data: Dict[str, Any]) -> MatchAnalysis:
        try:
            prompt = build_job_match_prompt(resume_version, job_data)
            response_text = await self.llm_provider.generate(prompt)
            logger.info("[MATCHER STAGE 1] Raw LLM response: %s", response_text)

            parsed_payload = self._safe_parse_response(response_text)
            logger.info("[MATCHER STAGE 2 & 3] Parsed & _normalize_payload result: %s", parsed_payload)

            match_analysis = self._validate_match_analysis(parsed_payload)
            logger.info("[MATCHER STAGE 5] Final MatchAnalysis.model_dump(): %s", match_analysis.model_dump())
            return match_analysis
        except (RuntimeError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.exception("Job matcher comparison hit an LLM transport failure")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI service is temporarily unavailable, please try again.",
            ) from exc

    async def compare_resume_job(self, resume_version: Dict[str, Any], job_data: Dict[str, Any]) -> MatchComparisonResponse:
        try:
            prompt = build_job_match_prompt(resume_version, job_data)
            response_text = await self.llm_provider.generate(prompt)

            parsed_payload = self._safe_parse_response(response_text)
            return self._validate_match_response(parsed_payload)
        except (RuntimeError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.exception("Job match response generation hit an LLM transport failure")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI service is temporarily unavailable, please try again.",
            ) from exc

    def _safe_parse_response(self, response_text: str) -> Dict[str, Any]:
        content = response_text.strip()
        if not content:
            logger.error("Job matcher agent received empty response")
            raise ValueError("Empty response from job matcher agent")

        for attempt in range(2):
            try:
                payload = json.loads(content)
                logger.info("[MATCHER STAGE 2] Parsed JSON object successfully")
                return self._normalize_payload(payload)
            except json.JSONDecodeError as exc:
                logger.warning("Job matcher JSON decode failed at attempt %s: %s", attempt + 1, exc)
                content = self._extract_json_snippet(content)

        logger.error("Job matcher failed to parse JSON after retries: %s", response_text)
        raise ValueError("Unable to parse JSON from job matcher response")

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(payload)

        # Normalize overall_match_score from synonyms if missing or None
        score_keys = ["match_score", "score", "overall_score", "match_percentage", "compatibility_score", "overall_score_percentage"]
        for sk in score_keys:
            if sk in normalized and (normalized.get("overall_match_score") is None):
                val = normalized.pop(sk)
                try:
                    normalized["overall_match_score"] = float(val) if val is not None else None
                except (ValueError, TypeError):
                    pass

        if "ats_score" in normalized and normalized.get("ats_compatibility_score") is None:
            val = normalized.get("ats_score")
            try:
                normalized["ats_compatibility_score"] = float(val) if val is not None else None
            except (ValueError, TypeError):
                pass

        if "matched_skills" in normalized and normalized.get("skills_match") is None:
            normalized["skills_match"] = normalized.get("matched_skills")

        # Dictionary fields mapping list items to True
        dict_keys = ["matched_skills", "skills_match", "missing_skills", "missing_technologies", "missing_certifications"]
        for key in dict_keys:
            value = normalized.get(key)
            if isinstance(value, list):
                normalized[key] = {str(item): True for item in value if item is not None}
            elif value is None:
                normalized[key] = {}

        # String fields normalization
        string_keys = ["experience_gap", "education_gap", "final_recommendation"]
        for key in string_keys:
            if key in normalized:
                normalized[key] = normalize_string(normalized.get(key))

        return normalized

    def _extract_json_snippet(self, raw_text: str) -> str:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1 or end < start:
            return raw_text
        return raw_text[start : end + 1]

    def _validate_match_analysis(self, payload: Dict[str, Any]) -> MatchAnalysis:
        try:
            normalized_payload = normalize_payload_for_model(payload, MatchAnalysis)
            logger.info("[MATCHER STAGE 4] Payload after normalize_payload_for_model(): %s", normalized_payload)
            return MatchAnalysis.model_validate(normalized_payload)
        except ValidationError as exc:
            logger.error("Job matcher response validation failed: %s", exc)
            raise ValueError("Match analysis data failed validation") from exc


    def _validate_match_response(self, payload: Dict[str, Any]) -> MatchComparisonResponse:
        try:
            normalized_payload = normalize_payload_for_model(payload, MatchComparisonResponse)
            return MatchComparisonResponse.model_validate(normalized_payload)
        except ValidationError as exc:
            logger.error("Job matcher response validation failed: %s", exc)
            raise ValueError("Match response data failed validation") from exc
