import logging
import time
from typing import Any, Dict

from pydantic import ValidationError

from src.exceptions.ai_service import AIResponseParsingException, AIResponseValidationException
from src.infrastructure.llm.provider import LLMProvider
from src.prompts.strategy.roadmap_prompt import build_roadmap_prompt
from src.schemas.career_strategy import RoadmapPlan
from src.utils.json_repair import JSONParsingError, parse_and_repair_json
from src.utils.token_counter import estimate_tokens

logger = logging.getLogger("careerpilot.roadmap_agent")

# Max tokens for roadmap responses (4 roadmap arrays)
_MAX_TOKENS = 3000


class RoadmapAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def build_roadmap(
        self,
        gap_payload: Dict[str, Any],
        profile_payload: Dict[str, Any],
        context_payload: Dict[str, Any],
    ) -> RoadmapPlan:
        start_time = time.perf_counter()

        prompt = build_roadmap_prompt(gap_payload, profile_payload, context_payload)
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
            "[PERF] RoadmapAgent completed | model=%s | prompt_tokens=%d | "
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
            payload = parse_and_repair_json(response_text, agent_name="RoadmapAgent", finish_reason=finish_reason)
        except JSONParsingError as exc:
            logger.error("[FATAL] RoadmapAgent JSON parsing failed after all repair attempts.")
            raise AIResponseParsingException(
                f"RoadmapAgent: {exc.original_error}"
            ) from exc

        return self._validate_payload(payload)

    def _validate_payload(self, payload: Dict[str, Any]) -> RoadmapPlan:
        try:
            return RoadmapPlan.model_validate(self._normalize_payload(payload))
        except ValidationError as exc:
            logger.error("Roadmap response validation failed: %s", exc)
            raise AIResponseValidationException(
                f"Roadmap data failed schema validation: {exc}"
            ) from exc

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            payload = {}

        weekly = [self._normalize_step(item) for item in payload.get("weekly_roadmap", [])]
        monthly = [self._normalize_step(item) for item in payload.get("monthly_roadmap", [])]
        quarterly = [self._normalize_step(item) for item in payload.get("quarterly_roadmap", [])]
        roadmap = [self._normalize_step(item) for item in payload.get("roadmap", [])]

        if not roadmap:
            roadmap = [
                self._normalize_step({
                    "title": "Foundational skill building",
                    "topic": "Core skill development",
                    "duration_weeks": 2,
                    "priority": "high",
                    "dependencies": [],
                    "expected_outcomes": ["Improved readiness"],
                    "timeframe": "Next 2 weeks",
                })
            ]

        if not weekly:
            weekly = roadmap[:1]
        if not monthly:
            monthly = roadmap[:1]
        if not quarterly:
            quarterly = roadmap[:1]

        return {
            "weekly_roadmap": weekly,
            "monthly_roadmap": monthly,
            "quarterly_roadmap": quarterly,
            "roadmap": roadmap,
        }

    def _normalize_step(self, item: Any) -> Dict[str, Any]:
        if isinstance(item, dict):
            return {
                "title": str(item.get("title", "")),
                "topic": str(item.get("topic", "")),
                "duration_weeks": int(item.get("duration_weeks", 1) or 1),
                "priority": str(item.get("priority", "medium")),
                "dependencies": [str(dep) for dep in item.get("dependencies", [])],
                "expected_outcomes": [str(outcome) for outcome in item.get("expected_outcomes", [])],
                "timeframe": str(item.get("timeframe", "TBD")),
            }
        return {
            "title": str(item),
            "topic": "",
            "duration_weeks": 1,
            "priority": "medium",
            "dependencies": [],
            "expected_outcomes": [],
            "timeframe": "TBD",
        }