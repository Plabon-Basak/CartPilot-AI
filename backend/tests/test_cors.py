from fastapi.testclient import TestClient

from main import app


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


def test_cors_unapproved_origin():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Unapproved origin should not be granted CORS access
    assert response.headers.get("access-control-allow-origin") != "http://evil.example.com"


def test_existing_endpoints_still_work():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
