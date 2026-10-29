
from urllib import response

import httpx

from app.config import settings


def get_paypal_access_token():
    if settings.paypal_mode.lower() != "sandbox":
        raise ValueError("Only PayPal Sandbox mode is allowed.")

    response = httpx.post(
        f"{settings.paypal_base_url}/v1/oauth2/token",
        auth=(
            settings.paypal_client_id,
            settings.paypal_client_secret
        ),
        data={"grant_type": "client_credentials"},
        headers={"Accept": "application/json"},
        timeout=20.0
    )

    response.raise_for_status()

    return response.json()["access_token"]


def create_paypal_order(amount="10.00", currency="USD"):
    if settings.paypal_mode.lower() != "sandbox":
        raise ValueError("Only PayPal Sandbox mode is allowed.")

    access_token = get_paypal_access_token()

    response = httpx.post(
        f"{settings.paypal_base_url}/v2/checkout/orders",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": currency,
                        "value": amount
                    }
                }
            ],
            "application_context": {
                "return_url": f"{getattr(settings, 'frontend_return_url', 'http://localhost:5173/?paypal=return')}",
                "cancel_url": f"{getattr(settings, 'frontend_cancel_url', 'http://localhost:5173/?paypal=cancel')}",
                "user_action": "PAY_NOW",
                "shipping_preference": "NO_SHIPPING"
            }
        },
        timeout=20.0
    )

    if not response.is_success:
        raise RuntimeError(
            f"PayPal API error {response.status_code}: "
            f"{response.text[:1000]}"
        )

    order = response.json()

    return {
        "id": order["id"],
        "status": order["status"],
        "links": [
            {
                "rel": link["rel"],
                "href": link["href"]
            }
            for link in order.get("links", [])
        ]
    }


def get_paypal_order(order_id: str):
    if settings.paypal_mode.lower() != "sandbox":
        raise ValueError("Only PayPal Sandbox mode is allowed.")

    access_token = get_paypal_access_token()

    response = httpx.get(
        f"{settings.paypal_base_url}/v2/checkout/orders/{order_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        timeout=20.0
    )

    response.raise_for_status()

    order = response.json()

    return {
        "id": order["id"],
        "status": order["status"],
        "intent": order["intent"],
        "amount": order["purchase_units"][0]["amount"]
    }


def verify_paypal_approval(order_id: str):
    order = get_paypal_order(order_id)

    return {
        "id": order["id"],
        "status": order["status"],
        "approved": order["status"] == "APPROVED"
    }


def capture_paypal_order(order_id: str):
    if settings.paypal_mode.lower() != "sandbox":
        raise ValueError("Only PayPal Sandbox mode is allowed.")

    order = get_paypal_order(order_id)

    if order["status"] != "APPROVED":
        raise ValueError("PayPal order has not been approved.")

    access_token = get_paypal_access_token()

    response = httpx.post(
        f"{settings.paypal_base_url}/v2/checkout/orders/{order_id}/capture",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        timeout=20.0
    )

    response.raise_for_status()

    result = response.json()

    return {
        "id": result["id"],
        "status": result["status"]
    }
