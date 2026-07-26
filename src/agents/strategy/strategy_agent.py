import logging
import time
from typing import Any, Dict, Tuple

from pydantic import ValidationError

from src.exceptions.ai_service import AIResponseParsingException, AIResponseValidationException
from src.infrastructure.llm.provider import LLMProvider
from src.prompts.strategy.strategy_prompt import build_strategy_prompt
from src.schemas.career_strategy import CareerStrategyCreate
from src.utils.json_repair import JSONParsingError, parse_and_repair_json
from src.utils.token_counter import estimate_tokens

logger = logging.getLogger("careerpilot.strategy_agent")

# Max tokens for strategy responses (large schema with many nested arrays)
_MAX_TOKENS = 4096
# Retry max_tokens if first attempt is truncated
_RETRY_MAX_TOKENS = 6000


class StrategyAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def build_strategy(
        self,
        gap_payload: Dict[str, Any],
        roadmap_payload: Dict[str, Any],
        profile_payload: Dict[str, Any],
        context_payload: Dict[str, Any],
    ) -> CareerStrategyCreate:
        start_time = time.perf_counter()
        prompt = build_strategy_prompt(gap_payload, roadmap_payload, profile_payload, context_payload)
        prompt_tokens = estimate_tokens(prompt)

        # --- Attempt 1: Standard generation ---
        response_text, metadata, finish_reason = await self._generate_with_diagnostics(
            prompt, prompt_tokens, max_tokens=_MAX_TOKENS,
        )

        # -------- LOG RAW RESPONSE AT ERROR LEVEL --------
        logger.error(
            "\n========== RAW RESPONSE (StrategyAgent) ==========\n%s\n=======================================",
            response_text,
        )

        # --- Attempt 2: If truncated, retry with higher token budget ---
        if finish_reason == "length":
            logger.warning(
                "[RETRY] StrategyAgent response was truncated. Retrying with max_tokens=%d",
                _RETRY_MAX_TOKENS,
            )
            response_text, metadata, finish_reason = await self._generate_with_diagnostics(
                prompt, prompt_tokens, max_tokens=_RETRY_MAX_TOKENS,
            )
            if finish_reason == "length":
                logger.warning(
                    "[RETRY TRUNCATED] StrategyAgent retry was also truncated. Proceeding with best-effort parsing.",
                )

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info("[PERF] StrategyAgent total pipeline duration=%.2fms", duration_ms)

        try:
            payload = parse_and_repair_json(response_text, agent_name="StrategyAgent", finish_reason=finish_reason)
        except JSONParsingError as exc:
            logger.error("[FATAL] StrategyAgent JSON parsing failed after all repair attempts.")
            raise AIResponseParsingException(
                f"StrategyAgent: {exc.original_error}"
            ) from exc

        return self._validate_payload(payload)

    async def _generate_with_diagnostics(
        self, prompt: str, prompt_tokens: int, max_tokens: int
    ) -> Tuple[str, Dict[str, Any], str]:
        """Generate LLM response with full diagnostic logging. Returns (response_text, metadata, finish_reason)."""
        start = time.perf_counter()

        if hasattr(self.llm_provider, "generate_with_metadata"):
            response_text, metadata = await self.llm_provider.generate_with_metadata(
                prompt, max_tokens=max_tokens,
            )
            finish_reason = metadata.get("finish_reason")
            model = metadata.get("model", "unknown")
            api_prompt_tokens = metadata.get("prompt_tokens")
            api_completion_tokens = metadata.get("completion_tokens")
        else:
            response_text = await self.llm_provider.generate(prompt, max_tokens=max_tokens)
            metadata = {}
            finish_reason = None
            model = "unknown"
            api_prompt_tokens = None
            api_completion_tokens = None

        gen_ms = (time.perf_counter() - start) * 1000
        completion_tokens = estimate_tokens(response_text)

        logger.info(
            "[PERF] StrategyAgent LLM call | model=%s | prompt_tokens=%d | "
            "completion_tokens=%d | api_prompt_tokens=%s | api_completion_tokens=%s | "
            "finish_reason=%s | max_tokens=%d | duration=%.2fms | response_length=%d",
            model,
            prompt_tokens,
            completion_tokens,
            api_prompt_tokens,
            api_completion_tokens,
            finish_reason or "unknown",
            max_tokens,
            gen_ms,
            len(response_text) if response_text else 0,
        )

        return response_text, metadata, finish_reason

    def _safe_parse_response(self, response_text: str, finish_reason: str = None) -> Dict[str, Any]:
        return parse_and_repair_json(response_text, agent_name="StrategyAgent", finish_reason=finish_reason)

    def _validate_payload(self, payload: Dict[str, Any]) -> CareerStrategyCreate:
        try:
            return CareerStrategyCreate.model_validate(self._normalize_payload(payload))
        except ValidationError as exc:
            logger.error("Strategy response validation failed: %s", exc)
            raise AIResponseValidationException(
                f"Strategy data failed schema validation: {exc}"
            ) from exc

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            payload = {}
        recommendations = payload.get("recommendations", [])
        if not recommendations:
            recommendations = [{"title": "Build a focused learning plan", "reason": "Prioritize your highest-impact skill gaps"}]
        roadmap_data = payload.get("roadmap", {})
        if isinstance(roadmap_data, list):
            roadmap_data = {"roadmap": roadmap_data}

        return {
            "user_id": payload.get("user_id"),
            "strategy_version": payload.get("strategy_version", 1),
            "skill_gap_analysis": payload.get("skill_gap_analysis", {}) if isinstance(payload.get("skill_gap_analysis"), dict) else {},
            "roadmap": roadmap_data if isinstance(roadmap_data, dict) else {},
            "certifications": payload.get("certifications", []) if isinstance(payload.get("certifications"), list) else [],
            "projects": payload.get("projects", []) if isinstance(payload.get("projects"), list) else [],
            "weekly_goals": payload.get("weekly_goals", []) if isinstance(payload.get("weekly_goals"), list) else [],
            "monthly_goals": payload.get("monthly_goals", []) if isinstance(payload.get("monthly_goals"), list) else [],
            "progress_snapshot": payload.get("progress_snapshot", {"completed_items": 0, "progress_percent": 0.0, "goal_completion": {"weekly": 0.0, "monthly": 0.0}}) if isinstance(payload.get("progress_snapshot"), dict) else {"completed_items": 0, "progress_percent": 0.0, "goal_completion": {"weekly": 0.0, "monthly": 0.0}},
            "refresh_count": payload.get("refresh_count", 0),
            "strategy_id": payload.get("strategy_id") or "strategy-1",
            "recommendations": recommendations if isinstance(recommendations, list) else [],
        }