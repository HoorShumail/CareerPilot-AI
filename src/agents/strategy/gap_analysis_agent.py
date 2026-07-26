import logging
import time
from typing import Any, Dict

from pydantic import ValidationError

from src.exceptions.ai_service import AIResponseParsingException, AIResponseValidationException
from src.infrastructure.llm.provider import LLMProvider
from src.prompts.strategy.gap_analysis_prompt import build_gap_analysis_prompt
from src.schemas.career_strategy import SkillGapAnalysis
from src.utils.json_repair import JSONParsingError, parse_and_repair_json
from src.utils.token_counter import estimate_tokens

logger = logging.getLogger("careerpilot.gap_analysis_agent")

# Max tokens for gap analysis responses (schema is compact)
_MAX_TOKENS = 2048


class GapAnalysisAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def analyze(self, profile_payload: Dict[str, Any], context_payload: Dict[str, Any]) -> SkillGapAnalysis:
        start_time = time.perf_counter()
        prompt = build_gap_analysis_prompt(profile_payload, context_payload)
        prompt_tokens = estimate_tokens(prompt)

        # Use generate_with_metadata to capture finish_reason
        if hasattr(self.llm_provider, "generate_with_metadata"):
            response_text, metadata = await self.llm_provider.generate_with_metadata(
                prompt, max_tokens=_MAX_TOKENS,
            )
            finish_reason = metadata.get("finish_reason")
            model = metadata.get("model", "unknown")
            api_prompt_tokens = metadata.get("prompt_tokens")
            api_completion_tokens = metadata.get("completion_tokens")
        else:
            response_text = await self.llm_provider.generate(prompt, max_tokens=_MAX_TOKENS)
            finish_reason = None
            model = "unknown"
            api_prompt_tokens = None
            api_completion_tokens = None

        duration_ms = (time.perf_counter() - start_time) * 1000
        completion_tokens = estimate_tokens(response_text)

        logger.info(
            "[PERF] GapAnalysisAgent completed | model=%s | prompt_tokens=%d | "
            "completion_tokens=%d | api_prompt_tokens=%s | api_completion_tokens=%s | "
            "finish_reason=%s | duration=%.2fms | response_length=%d",
            model,
            prompt_tokens,
            completion_tokens,
            api_prompt_tokens,
            api_completion_tokens,
            finish_reason or "unknown",
            duration_ms,
            len(response_text) if response_text else 0,
        )

        try:
            payload = parse_and_repair_json(response_text, agent_name="GapAnalysisAgent", finish_reason=finish_reason)
        except JSONParsingError as exc:
            logger.error("[FATAL] GapAnalysisAgent JSON parsing failed after all repair attempts.")
            raise AIResponseParsingException(
                f"GapAnalysisAgent: {exc.original_error}"
            ) from exc

        return self._validate_payload(payload)

    def _validate_payload(self, payload: Dict[str, Any]) -> SkillGapAnalysis:
        try:
            return SkillGapAnalysis.model_validate(self._normalize_payload(payload))
        except ValidationError as exc:
            logger.error("Gap analysis response validation failed: %s", exc)
            raise AIResponseValidationException(
                f"Gap analysis data failed schema validation: {exc}"
            ) from exc

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            payload = {}
        return {
            "gaps": [self._normalize_gap_item(item) for item in payload.get("gaps", [])],
            "weak_skills": [self._normalize_gap_item(item) for item in payload.get("weak_skills", [])],
            "emerging_skills": [self._normalize_gap_item(item) for item in payload.get("emerging_skills", [])],
            "priority_skills": [str(item) for item in payload.get("priority_skills", [])],
        }

    def _normalize_gap_item(self, item: Any) -> Dict[str, Any]:
        if isinstance(item, dict):
            return {
                "skill": str(item.get("skill", "")),
                "severity": str(item.get("severity", "medium")),
                "reason": str(item.get("reason", "No reason provided")),
            }
        return {"skill": str(item), "severity": "medium", "reason": "No reason provided"}
