
import asyncio
import logging
import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app import gemini
from app import config


def _success_response(text: str = "Hello from Gemini") -> AsyncMock:
    mock_response = AsyncMock()
    mock_response.is_success = True
    mock_response.json = AsyncMock(return_value={
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": text}
                    ]
                }
            }
        ]
    })
    return mock_response


def _status_response(status_code: int) -> AsyncMock:
    mock_response = AsyncMock()
    mock_response.is_success = False
    mock_response.status_code = status_code
    mock_response.text = "SENSITIVE_UPSTREAM_BODY"
    return mock_response


def test_generate_response_success():
    mock_response = AsyncMock()
    mock_response.is_success = True
    mock_response.json = AsyncMock(return_value={
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Hello from Gemini"}
                    ]
                }
            }
        ]
    })

    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            result = asyncio.run(gemini.generate_response("Hi"))
            assert result == "Hello from Gemini"


def test_generate_response_missing_api_key():
    with patch.object(config.settings, "gemini_api_key", None):
        with pytest.raises(ValueError) as exc:
            asyncio.run(gemini.generate_response("Hi"))

        assert "not configured" in str(exc.value).lower()


def test_generate_response_api_error_does_not_expose_body(caplog):
    caplog.set_level(logging.INFO, logger="app.gemini")
    mock_response = _status_response(400)

    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with pytest.raises(RuntimeError) as exc:
                asyncio.run(gemini.generate_response("Hi"))

    assert str(exc.value) == "Gemini API error 400"
    assert "SENSITIVE_UPSTREAM_BODY" not in str(exc.value)
    assert "SENSITIVE_UPSTREAM_BODY" not in caplog.text
    assert "status=400" in caplog.text


def test_generate_response_malformed_empty():
    mock_response = AsyncMock()
    mock_response.is_success = True
    mock_response.json = AsyncMock(return_value={"candidates": []})

    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with pytest.raises((RuntimeError, ValueError)):
                asyncio.run(gemini.generate_response("Hi"))


def test_generate_response_retries_after_503():
    success_response = AsyncMock()
    success_response.is_success = True
    success_response.json = AsyncMock(return_value={
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Recovered response"}
                    ]
                }
            }
        ]
    })

    temporary_error = AsyncMock()
    temporary_error.is_success = False
    temporary_error.status_code = 503
    temporary_error.text = "Service unavailable"

    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(
            side_effect=[temporary_error, success_response]
        )
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with patch(
                "app.gemini.asyncio.sleep",
                new_callable=AsyncMock
            ):
                result = asyncio.run(gemini.generate_response("Hi"))

        assert result == "Recovered response"
        assert mock_client.post.await_count == 2


def test_generate_response_stops_after_three_attempts():
    temporary_error = AsyncMock()
    temporary_error.is_success = False
    temporary_error.status_code = 503
    temporary_error.text = "Service unavailable"

    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=temporary_error)
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with patch(
                "app.gemini.asyncio.sleep",
                new_callable=AsyncMock
            ):
                with pytest.raises(
                    RuntimeError,
                    match="Gemini API error 503"
                ):
                    asyncio.run(gemini.generate_response("Hi"))

        assert mock_client.post.await_count == 3


def test_generate_response_requests_low_thinking_level():
    mock_response = _success_response()

    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            asyncio.run(gemini.generate_response("Hi"))

        payload = mock_client.post.await_args.kwargs["json"]

    thinking = payload["generationConfig"]["thinkingConfig"]
    assert thinking["thinkingLevel"] == "low"


def test_generate_response_omits_thinking_for_gemini_2_5_model():
    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=_success_response())
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with patch.object(
                config.settings,
                "gemini_model",
                "gemini-2.5-flash",
            ):
                asyncio.run(gemini.generate_response("Hi"))

        payload = mock_client.post.await_args.kwargs["json"]
        url = mock_client.post.await_args.args[0]

    assert "generationConfig" not in payload
    assert "gemini-2.5-flash" in url


def test_generate_response_uses_thinking_compatible_fallback_model():
    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=_success_response())
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with patch.object(config.settings, "gemini_model", ""):
                asyncio.run(gemini.generate_response("Hi"))

        payload = mock_client.post.await_args.kwargs["json"]
        url = mock_client.post.await_args.args[0]

    assert gemini.FALLBACK_GEMINI_MODEL in url
    assert payload["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "low"


def test_read_timeout_is_not_retried():
    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(
            side_effect=httpx.ReadTimeout("read timed out")
        )
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with patch(
                "app.gemini.asyncio.sleep",
                new_callable=AsyncMock
            ) as mock_sleep:
                with pytest.raises(
                    gemini.GeminiTimeoutError,
                    match="Gemini request timed out",
                ):
                    asyncio.run(gemini.generate_response("Hi"))

    assert mock_client.post.await_count == 1
    mock_sleep.assert_not_awaited()


def test_connect_error_is_retried_and_can_recover():
    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(side_effect=[
            httpx.ConnectError("connection failed"),
            _success_response("Recovered response"),
        ])
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with patch(
                "app.gemini.asyncio.sleep",
                new_callable=AsyncMock
            ):
                result = asyncio.run(gemini.generate_response("Hi"))

    assert result == "Recovered response"
    assert mock_client.post.await_count == 2


def test_network_error_stops_after_three_attempts():
    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(
            side_effect=httpx.ConnectError("connection failed")
        )
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with patch(
                "app.gemini.asyncio.sleep",
                new_callable=AsyncMock
            ):
                with pytest.raises(
                    RuntimeError,
                    match="Gemini request failed after 3 attempt",
                ):
                    asyncio.run(gemini.generate_response("Hi"))

    assert mock_client.post.await_count == 3


@pytest.mark.parametrize(
    "exception_type",
    [httpx.ConnectTimeout, httpx.WriteTimeout, httpx.PoolTimeout],
)
def test_request_timeout_exception_is_retried_and_can_recover(exception_type):
    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(side_effect=[
            exception_type("request timed out"),
            _success_response("Recovered response"),
        ])
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with patch(
                "app.gemini.asyncio.sleep",
                new_callable=AsyncMock
            ) as mock_sleep:
                result = asyncio.run(gemini.generate_response("Hi"))

    assert result == "Recovered response"
    assert mock_client.post.await_count == 2
    assert mock_sleep.await_count == 1


@pytest.mark.parametrize(
    "exception_type",
    [httpx.ConnectTimeout, httpx.WriteTimeout, httpx.PoolTimeout],
)
def test_request_timeout_exception_stops_after_three_attempts(exception_type):
    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(
            side_effect=exception_type("request timed out")
        )
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with patch(
                "app.gemini.asyncio.sleep",
                new_callable=AsyncMock
            ) as mock_sleep:
                with pytest.raises(gemini.GeminiTimeoutError):
                    asyncio.run(gemini.generate_response("Hi"))

    assert mock_client.post.await_count == 3
    assert mock_sleep.await_count == 2


def test_total_budget_timeout_during_in_flight_request():
    async def slow_post(*args, **kwargs):
        await asyncio.sleep(5)

    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(side_effect=slow_post)
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with patch.object(
                gemini,
                "TOTAL_REQUEST_BUDGET_SECONDS",
                0.2,
            ):
                started = time.monotonic()
                with pytest.raises(gemini.GeminiTimeoutError):
                    asyncio.run(gemini.generate_response("Hi"))
                elapsed = time.monotonic() - started

    assert elapsed < 1.0
    assert mock_client.post.await_count == 1


def test_total_budget_timeout_after_retries():
    call_count = 0

    async def fake_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return _status_response(503)
        await asyncio.sleep(5)

    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(side_effect=fake_post)
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with patch.object(gemini, "TOTAL_REQUEST_BUDGET_SECONDS", 0.5):
                with patch.object(gemini, "RETRY_DELAYS", (0.01, 0.01)):
                    started = time.monotonic()
                    with pytest.raises(gemini.GeminiTimeoutError):
                        asyncio.run(gemini.generate_response("Hi"))
                    elapsed = time.monotonic() - started

    assert elapsed < 2.0
    assert call_count == 3


def test_budget_exhaustion_prevents_retry_sleep():
    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=_status_response(503))
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with patch.object(gemini, "TOTAL_REQUEST_BUDGET_SECONDS", 0.01):
                with patch.object(gemini, "RETRY_DELAYS", (5.0, 5.0)):
                    with patch(
                        "app.gemini.asyncio.sleep",
                        new_callable=AsyncMock
                    ) as mock_sleep:
                        with pytest.raises(gemini.GeminiTimeoutError):
                            asyncio.run(gemini.generate_response("Hi"))

    assert mock_client.post.await_count == 1
    mock_sleep.assert_not_awaited()


def test_logs_do_not_contain_api_key_or_prompt(caplog):
    caplog.set_level(logging.INFO, logger="app.gemini")
    api_key = "API_KEY_SECRET_SENTINEL"
    prompt = "PROMPT_SECRET_SENTINEL"

    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=_success_response())
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", api_key):
            asyncio.run(gemini.generate_response(prompt))

    assert api_key not in caplog.text
    assert prompt not in caplog.text
