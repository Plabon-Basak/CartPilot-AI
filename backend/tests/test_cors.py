from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from main import _add_cors_middleware, _parse_cors_origins, app


client = TestClient(app)


def test_cors_allowed_origin():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_allowed_origin_127():
    response = client.options(
        "/products",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"


def test_cors_configured_origin_is_allowed(monkeypatch):
    monkeypatch.setenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:5173, https://cartpilot.vercel.app, , ",
    )
    configured_settings = Settings(
        _env_file=None,
        paypal_client_id="test-client-id",
        paypal_client_secret="test-client-secret",
    )
    origins = _parse_cors_origins(configured_settings.cors_allow_origins)

    assert origins == [
        "http://localhost:5173",
        "https://cartpilot.vercel.app",
    ]

    configured_app = FastAPI()

    @configured_app.get("/health")
    def configured_health():
        return {"status": "healthy"}

    _add_cors_middleware(configured_app, origins)
    configured_client = TestClient(configured_app)

    response = configured_client.options(
        "/health",
        headers={
            "Origin": "https://cartpilot.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://cartpilot.vercel.app"


def test_cors_unapproved_origin():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert response.headers.get("access-control-allow-origin") is None


def test_existing_endpoints_still_work():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
