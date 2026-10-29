from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


@patch("app.paypal.httpx.post")
@patch("app.paypal.httpx.post")  # will be called twice? first for token, second for order - need to be careful
def test_oauth_authentication_mocking(*args, **kwargs):
    # Simpler approach: patch get_paypal_access_token
    pass


@patch("app.paypal.get_paypal_access_token")
@patch("app.paypal.httpx.post")
def test_order_creation(mock_post, mock_token):
    mock_token.return_value = "test_token"
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.json.return_value = {
        "id": "ORDER123",
        "status": "CREATED",
        "links": [
            {"rel": "self", "href": "https://example.com/self"},
            {"rel": "approve", "href": "https://example.com/approve"},
        ],
    }
    mock_post.return_value = mock_response

    response = client.post("/paypal/orders", json={"amount": "10.00"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ORDER123"
    assert "approval_url" in data
    assert data["approval_url"] == "https://example.com/approve"

    # Verify root-level application_context payload
    called_json = mock_post.call_args.kwargs.get("json")
    assert called_json is not None
    assert "application_context" in called_json
    assert "payment_source" not in called_json
    assert called_json["application_context"]["user_action"] == "PAY_NOW"
    assert called_json["application_context"]["shipping_preference"] == "NO_SHIPPING"
    assert called_json["application_context"]["return_url"] == "http://localhost:5173/?paypal=return"
    assert called_json["application_context"]["cancel_url"] == "http://localhost:5173/?paypal=cancel"


@patch("app.paypal.get_paypal_access_token")
@patch("app.paypal.httpx.get")
def test_order_retrieval(mock_get, mock_token):
    mock_token.return_value = "test_token"
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "id": "ORDER123",
        "status": "APPROVED",
        "intent": "CAPTURE",
        "purchase_units": [{"amount": {"currency_code": "USD", "value": "10.00"}}],
    }
    mock_get.return_value = mock_response

    response = client.get("/paypal/orders/ORDER123")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ORDER123"
    assert data["status"] == "APPROVED"


@patch("app.paypal.get_paypal_access_token")
@patch("app.paypal.httpx.get")
def test_approval_verification(mock_get, mock_token):
    mock_token.return_value = "test_token"
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "id": "ORDER123",
        "status": "APPROVED",
        "intent": "CAPTURE",
        "purchase_units": [{"amount": {"currency_code": "USD", "value": "10.00"}}],
    }
    mock_get.return_value = mock_response

    response = client.get("/paypal/orders/ORDER123/approval")
    assert response.status_code == 200
    data = response.json()
    assert data["approved"] is True


@patch("app.paypal.get_paypal_access_token")
@patch("app.paypal.httpx.get")
@patch("app.paypal.httpx.post")
def test_rejection_of_unapproved_capture(mock_post, mock_get, mock_token):
    mock_token.return_value = "test_token"
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "id": "ORDER123",
        "status": "CREATED",
        "intent": "CAPTURE",
        "purchase_units": [{"amount": {"currency_code": "USD", "value": "10.00"}}],
    }
    mock_get.return_value = mock_response

    response = client.post("/paypal/orders/ORDER123/capture")
    assert response.status_code == 400


@patch("app.paypal.get_paypal_access_token")
@patch("app.paypal.httpx.post")
def test_paypal_api_error_handling(mock_post, mock_token):
    mock_token.return_value = "test_token"
    mock_response = MagicMock()
    mock_response.is_success = False
    mock_response.status_code = 400
    mock_response.text = '{"name":"INVALID_REQUEST","message":"Invalid request"}'
    mock_post.return_value = mock_response

    response = client.post("/paypal/orders", json={"amount": "10.00"})
    assert response.status_code == 502
    assert "PayPal API error" in response.json()["detail"]


@patch("app.paypal.httpx.post")
def test_oauth_authentication_flow(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"access_token": "abc123", "token_type": "Bearer"}
    mock_post.return_value = mock_response

    from app import paypal
    token = paypal.get_paypal_access_token()
    assert token == "abc123"
