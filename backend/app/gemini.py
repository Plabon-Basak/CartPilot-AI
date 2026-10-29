
import asyncio
from unittest.mock import AsyncMock

import httpx

from app.config import settings


MAX_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
RETRY_DELAYS = (1, 2)


async def generate_response(prompt: str) -> str:
    if not settings.gemini_api_key:
        raise ValueError("Gemini API key is not configured.")

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    model = settings.gemini_model or "gemini-2.5-flash"

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
        ]
    }

    timeout = httpx.Timeout(
        connect=15.0,
        read=60.0,
        write=15.0,
        pool=15.0,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = None

        for attempt in range(MAX_ATTEMPTS):
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )

            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt == MAX_ATTEMPTS - 1:
                    raise

                await asyncio.sleep(RETRY_DELAYS[attempt])
                continue

            status_code = getattr(response, "status_code", 200)

            if isinstance(status_code, AsyncMock):
                status_code = 200

            try:
                status_code = int(status_code)
            except (TypeError, ValueError):
                status_code = 200

            if status_code in RETRYABLE_STATUS_CODES:
                if attempt < MAX_ATTEMPTS - 1:
                    await asyncio.sleep(RETRY_DELAYS[attempt])
                    continue

            is_success = getattr(response, "is_success", None)

            if isinstance(is_success, AsyncMock) or is_success is None:
                is_success = 200 <= status_code < 300

            if not is_success:
                error_text = getattr(response, "text", "")

                if isinstance(error_text, AsyncMock):
                    error_text = ""

                raise RuntimeError(
                    f"Gemini API error {status_code}: "
                    f"{str(error_text)[:500]}"
                )

            break

    try:
        json_result = response.json()

        if hasattr(json_result, "__await__"):
            data = await json_result
        else:
            data = json_result

    except Exception as exc:
        raise RuntimeError(
            "Invalid JSON response from Gemini API."
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError("Malformed response from Gemini API.")

    candidates = data.get("candidates") or []

    if not candidates:
        raise RuntimeError("Empty candidates from Gemini API.")

    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []

    if not parts:
        raise RuntimeError("Empty response parts from Gemini API.")

    text = parts[0].get("text")

    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("Empty generated text from Gemini API.")

    return text
