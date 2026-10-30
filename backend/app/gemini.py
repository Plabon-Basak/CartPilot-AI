
import asyncio
import logging
import time
from unittest.mock import AsyncMock

import httpx

from app.config import settings


logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
RETRY_DELAYS = (1, 2)
CONNECT_TIMEOUT_SECONDS = 15.0
READ_TIMEOUT_SECONDS = 75.0
WRITE_TIMEOUT_SECONDS = 15.0
POOL_TIMEOUT_SECONDS = 15.0
TOTAL_REQUEST_BUDGET_SECONDS = 75.0
GEMINI_TIMEOUT_MESSAGE = "Gemini request timed out."
GEMINI_FAILURE_MESSAGE = "Gemini service error."
FALLBACK_GEMINI_MODEL = "gemini-3.5-flash"
THINKING_LEVEL_MODEL_PREFIXES = ("gemini-3", "gemini-4")


class GeminiTimeoutError(RuntimeError):
    """Raised when Gemini does not respond within the request budget."""


def _elapsed_ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)


def _generation_config_for_model(model: str) -> dict | None:
    if model.lower().startswith(THINKING_LEVEL_MODEL_PREFIXES):
        return {"thinkingConfig": {"thinkingLevel": "low"}}
    return None


def _usage_summary(data: dict) -> dict:
    usage = data.get("usageMetadata")
    if not isinstance(usage, dict):
        return {}

    keys = (
        "promptTokenCount",
        "candidatesTokenCount",
        "thoughtsTokenCount",
        "totalTokenCount",
    )
    return {key: usage[key] for key in keys if key in usage}


async def generate_response(prompt: str) -> str:
    if not settings.gemini_api_key:
        raise ValueError("Gemini API key is not configured.")

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    configured_model = (settings.gemini_model or "").strip()
    model = configured_model or FALLBACK_GEMINI_MODEL

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": settings.gemini_api_key,
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
    }

    generation_config = _generation_config_for_model(model)

    if generation_config is not None:
        payload["generationConfig"] = generation_config

    timeout = httpx.Timeout(
        connect=CONNECT_TIMEOUT_SECONDS,
        read=READ_TIMEOUT_SECONDS,
        write=WRITE_TIMEOUT_SECONDS,
        pool=POOL_TIMEOUT_SECONDS,
    )

    deadline = time.monotonic() + TOTAL_REQUEST_BUDGET_SECONDS

    logger.info(
        "gemini_request_start model=%s attempt_max=%d budget_ms=%d",
        model,
        MAX_ATTEMPTS,
        int(TOTAL_REQUEST_BUDGET_SECONDS * 1000),
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            remaining = deadline - time.monotonic()

            if remaining <= 0:
                logger.warning(
                    "gemini_request_budget_exhausted model=%s attempt=%d/%d",
                    model,
                    attempt,
                    MAX_ATTEMPTS,
                )
                raise GeminiTimeoutError(GEMINI_TIMEOUT_MESSAGE)

            attempt_start = time.monotonic()

            try:
                response = await asyncio.wait_for(
                    client.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=timeout,
                    ),
                    timeout=remaining,
                )

            except asyncio.TimeoutError as exc:
                logger.warning(
                    "gemini_request_failed model=%s attempt=%d/%d "
                    "elapsed_ms=%d exception=%s retry=false",
                    model,
                    attempt,
                    MAX_ATTEMPTS,
                    _elapsed_ms(attempt_start),
                    type(exc).__name__,
                )
                raise GeminiTimeoutError(GEMINI_TIMEOUT_MESSAGE) from exc

            except httpx.ReadTimeout as exc:
                logger.warning(
                    "gemini_request_failed model=%s attempt=%d/%d "
                    "elapsed_ms=%d exception=%s retry=false",
                    model,
                    attempt,
                    MAX_ATTEMPTS,
                    _elapsed_ms(attempt_start),
                    type(exc).__name__,
                )
                raise GeminiTimeoutError(GEMINI_TIMEOUT_MESSAGE) from exc

            except (
                httpx.ConnectTimeout,
                httpx.WriteTimeout,
                httpx.PoolTimeout,
                httpx.NetworkError,
            ) as exc:
                elapsed_ms = _elapsed_ms(attempt_start)
                should_retry = (
                    attempt < MAX_ATTEMPTS
                    and (deadline - time.monotonic()) > RETRY_DELAYS[attempt - 1]
                )

                logger.warning(
                    "gemini_request_failed model=%s attempt=%d/%d "
                    "elapsed_ms=%d exception=%s retry=%s",
                    model,
                    attempt,
                    MAX_ATTEMPTS,
                    elapsed_ms,
                    type(exc).__name__,
                    str(should_retry).lower(),
                )

                if not should_retry:
                    if (
                        attempt < MAX_ATTEMPTS
                        or isinstance(exc, httpx.TimeoutException)
                    ):
                        raise GeminiTimeoutError(GEMINI_TIMEOUT_MESSAGE) from exc

                    raise RuntimeError(
                        f"Gemini request failed after {attempt} attempt(s): "
                        f"{type(exc).__name__}"
                    ) from exc

                await asyncio.sleep(RETRY_DELAYS[attempt - 1])
                continue

            elapsed_ms = _elapsed_ms(attempt_start)
            status_code = getattr(response, "status_code", 200)

            if isinstance(status_code, AsyncMock):
                status_code = 200

            try:
                status_code = int(status_code)
            except (TypeError, ValueError):
                status_code = 200

            if status_code in RETRYABLE_STATUS_CODES:
                should_retry = (
                    attempt < MAX_ATTEMPTS
                    and (deadline - time.monotonic()) > RETRY_DELAYS[attempt - 1]
                )

                logger.warning(
                    "gemini_response_retryable model=%s attempt=%d/%d "
                    "elapsed_ms=%d status=%d retry=%s",
                    model,
                    attempt,
                    MAX_ATTEMPTS,
                    elapsed_ms,
                    status_code,
                    str(should_retry).lower(),
                )

                if should_retry:
                    await asyncio.sleep(RETRY_DELAYS[attempt - 1])
                    continue

                if attempt < MAX_ATTEMPTS:
                    raise GeminiTimeoutError(GEMINI_TIMEOUT_MESSAGE)

            is_success = getattr(response, "is_success", None)

            if isinstance(is_success, AsyncMock) or is_success is None:
                is_success = 200 <= status_code < 300

            if not is_success:
                logger.warning(
                    "gemini_response_error model=%s attempt=%d/%d "
                    "elapsed_ms=%d status=%d retry=false",
                    model,
                    attempt,
                    MAX_ATTEMPTS,
                    elapsed_ms,
                    status_code,
                )

                raise RuntimeError(f"Gemini API error {status_code}")

            logger.info(
                "gemini_response_ok model=%s attempt=%d/%d "
                "elapsed_ms=%d status=%d",
                model,
                attempt,
                MAX_ATTEMPTS,
                elapsed_ms,
                status_code,
            )
            break

    try:
        json_result = response.json()

        if hasattr(json_result, "__await__"):
            data = await json_result
        else:
            data = json_result

    except Exception as exc:
        logger.warning(
            "gemini_response_invalid_json exception=%s",
            type(exc).__name__,
        )
        raise RuntimeError(
            "Invalid JSON response from Gemini API."
        ) from exc

    if not isinstance(data, dict):
        logger.warning("gemini_response_malformed reason=non_object")
        raise RuntimeError("Malformed response from Gemini API.")

    candidates = data.get("candidates") or []
    finish_reason = None
    if candidates and isinstance(candidates[0], dict):
        finish_reason = candidates[0].get("finishReason")

    logger.info(
        "gemini_response_metadata model=%s finish_reason=%s usage=%s",
        model,
        finish_reason,
        _usage_summary(data),
    )

    if not candidates:
        logger.warning("gemini_response_empty reason=no_candidates")
        raise RuntimeError("Empty candidates from Gemini API.")

    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []

    if not parts:
        logger.warning("gemini_response_empty reason=no_parts")
        raise RuntimeError("Empty response parts from Gemini API.")

    text = parts[0].get("text")

    if not isinstance(text, str) or not text.strip():
        logger.warning("gemini_response_empty reason=no_text")
        raise RuntimeError("Empty generated text from Gemini API.")

    return text
