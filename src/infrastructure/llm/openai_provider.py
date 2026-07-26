import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Type

import openai
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)

from src.infrastructure.llm.provider import LLMProvider
from src.utils.normalization import normalize_payload_for_model

logger = logging.getLogger("careerpilot.llm_provider")


class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: int = 60,
        embedding_model: str = "text-embedding-3-large",
    ):
        if not api_key:
            raise ValueError("LLM API key is required")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.embedding_model = embedding_model

        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=0,  # We manage retries explicitly with custom logging and error categorization
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response_format = kwargs.get("response_format", {"type": "json_object"})

        # Official OpenAI API requires the word 'json' in messages when response_format is json_object
        if isinstance(response_format, dict) and response_format.get("type") == "json_object":
            has_json = any("json" in m.get("content", "").lower() for m in messages)
            if not has_json:
                messages.insert(0, {"role": "system", "content": "You are a helpful assistant that responds in JSON format."})

        target_model = kwargs.get("model", self.model)
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.0),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "top_p": kwargs.get("top_p", 1.0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0),
            "response_format": response_format,
        }


        response = await self._call_with_retry(
            endpoint="/chat/completions",
            target_model=target_model,
            call_fn=lambda: self.client.chat.completions.create(**payload),
        )

        choices = getattr(response, "choices", [])
        if not choices:
            raise ValueError("No choices returned by LLM.")

        choice = choices[0]
        finish_reason = getattr(choice, "finish_reason", None)

        if finish_reason == "length":
            logger.warning(
                "[TOKEN TRUNCATION] LLM response was truncated (finish_reason='length'). "
                "Consider increasing max_tokens. model=%s",
                kwargs.get("model", self.model),
            )

        content = choice.message.content or ""
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )

        return str(content).strip()

    async def generate_with_metadata(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a raw string response alongside metadata (finish_reason, model, token usage).
        Agents should use this method to detect truncation and log diagnostics.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response_format = kwargs.get("response_format", {"type": "json_object"})

        if isinstance(response_format, dict) and response_format.get("type") == "json_object":
            has_json = any("json" in m.get("content", "").lower() for m in messages)
            if not has_json:
                messages.insert(0, {"role": "system", "content": "You are a helpful assistant that responds in JSON format."})

        target_model = kwargs.get("model", self.model)
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.0),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "top_p": kwargs.get("top_p", 1.0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0),
            "response_format": response_format,
        }

        response = await self._call_with_retry(
            endpoint="/chat/completions",
            target_model=target_model,
            call_fn=lambda: self.client.chat.completions.create(**payload),
        )

        choices = getattr(response, "choices", [])
        if not choices:
            raise ValueError("No choices returned by LLM.")

        choice = choices[0]
        finish_reason = getattr(choice, "finish_reason", None)
        usage = getattr(response, "usage", None)

        metadata = {
            "model": target_model,
            "finish_reason": finish_reason,
            "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
            "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
            "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
        }

        if finish_reason == "length":
            logger.warning(
                "[TOKEN TRUNCATION] LLM response truncated | model=%s | prompt_tokens=%s | completion_tokens=%s",
                target_model,
                metadata.get("prompt_tokens"),
                metadata.get("completion_tokens"),
            )

        content = choice.message.content or ""
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )

        return str(content).strip(), metadata

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Any,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        raw = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            **kwargs,
        )

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("LLM response was not valid JSON: %s", raw)
            raise ValueError("LLM did not return valid JSON.") from exc

        if hasattr(response_schema, "model_validate"):
            if isinstance(parsed, dict):
                parsed = normalize_payload_for_model(parsed, response_schema)
            return response_schema.model_validate(parsed)

        if isinstance(response_schema, type):
            return response_schema(**parsed)

        return parsed

    async def get_embeddings(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        target_model = self.embedding_model

        response = await self._call_with_retry(
            endpoint="/embeddings",
            target_model=target_model,
            call_fn=lambda: self.client.embeddings.create(
                model=target_model,
                input=texts,
            ),
        )

        data = getattr(response, "data", [])
        if not data:
            raise ValueError("No embeddings returned by LLM.")

        return [item.embedding for item in data]

    async def _call_with_retry(
        self,
        endpoint: str,
        target_model: str,
        call_fn: Any,
        max_retries: int = 3,
    ) -> Any:
        last_exception = None

        for attempt in range(1, max_retries + 1):
            start_time = time.perf_counter()
            try:
                response = await call_fn()
                duration = time.perf_counter() - start_time

                # Log metadata without prompts or sensitive info
                usage = getattr(response, "usage", None)
                tokens_info = f"prompt_tokens={usage.prompt_tokens}, completion_tokens={getattr(usage, 'completion_tokens', 0)}, total_tokens={usage.total_tokens}" if usage else "tokens=N/A"
                req_id = getattr(response, "_request_id", None) or "N/A"

                logger.info(
                    "OpenAI API Call Succeeded | endpoint=%s | model=%s | duration=%.3fs | request_id=%s | retries=%d | %s",
                    endpoint,
                    target_model,
                    duration,
                    req_id,
                    attempt - 1,
                    tokens_info,
                )
                return response

            except (AuthenticationError, PermissionDeniedError, NotFoundError, BadRequestError, UnprocessableEntityError) as exc:
                duration = time.perf_counter() - start_time
                logger.error(
                    "OpenAI API Non-Retryable Error | endpoint=%s | model=%s | duration=%.3fs | error_type=%s",
                    endpoint,
                    target_model,
                    duration,
                    type(exc).__name__,
                )
                raise self._map_exception(exc) from exc

            except (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError, APIError) as exc:
                duration = time.perf_counter() - start_time
                status_code = getattr(exc, "status_code", None)
                last_exception = exc

                is_transient = isinstance(exc, (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)) or (status_code in [429, 500, 502, 503, 504])

                if not is_transient or attempt == max_retries:
                    logger.error(
                        "OpenAI API Final Failure | endpoint=%s | model=%s | duration=%.3fs | attempt=%d/%d | error_type=%s",
                        endpoint,
                        target_model,
                        duration,
                        attempt,
                        max_retries,
                        type(exc).__name__,
                    )
                    raise self._map_exception(exc) from exc

                backoff = 2 ** attempt
                logger.warning(
                    "OpenAI API Transient Error, retrying in %ds | endpoint=%s | model=%s | duration=%.3fs | attempt=%d/%d | error=%s",
                    backoff,
                    endpoint,
                    target_model,
                    duration,
                    attempt,
                    max_retries,
                    type(exc).__name__,
                )
                await asyncio.sleep(backoff)

            except Exception as exc:
                duration = time.perf_counter() - start_time
                logger.exception(
                    "Unexpected error during OpenAI API call | endpoint=%s | model=%s | duration=%.3fs",
                    endpoint,
                    target_model,
                    duration,
                )
                raise RuntimeError("Unexpected error occurred while contacting AI service.") from exc

        raise self._map_exception(last_exception)

    def _map_exception(self, exc: Any) -> Exception:
        """Converts OpenAI exceptions into clean application errors."""
        if isinstance(exc, AuthenticationError):
            return RuntimeError("Invalid OpenAI API key or unauthorized request.")
        if isinstance(exc, PermissionDeniedError):
            return RuntimeError("OpenAI API permission denied.")
        if isinstance(exc, RateLimitError):
            return RuntimeError("OpenAI API rate limit exceeded. Please try again later.")
        if isinstance(exc, APITimeoutError):
            return RuntimeError("OpenAI API request timed out.")
        if isinstance(exc, APIConnectionError):
            return RuntimeError("The AI service connection failed. Please try again.")
        if isinstance(exc, InternalServerError):
            return RuntimeError("The AI service encountered an internal error.")
        if isinstance(exc, APIError):
            return RuntimeError("The AI service returned an error.")
        return RuntimeError("The AI service is temporarily unavailable, please try again.")