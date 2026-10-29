
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app import gemini
from app import config


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


def test_generate_response_api_error():
    mock_response = AsyncMock()
    mock_response.is_success = False
    mock_response.status_code = 400
    mock_response.text = '{"error":{"message":"Bad Request"}}'

    with patch("app.gemini.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        with patch.object(config.settings, "gemini_api_key", "test_key"):
            with pytest.raises(RuntimeError) as exc:
                asyncio.run(gemini.generate_response("Hi"))

            assert "Gemini API error" in str(exc.value)


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
