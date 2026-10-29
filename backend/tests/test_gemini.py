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
            import asyncio
            result = asyncio.run(gemini.generate_response("Hi"))
            assert result == "Hello from Gemini"


def test_generate_response_missing_api_key():
    with patch.object(config.settings, "gemini_api_key", None):
        import asyncio
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
            import asyncio
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
            import asyncio
            with pytest.raises((RuntimeError, ValueError)):
                asyncio.run(gemini.generate_response("Hi"))
