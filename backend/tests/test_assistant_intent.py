from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


@patch("main.generate_response")
def test_valid_shopping_intent_extraction(mock_gen):
    mock_gen.return_value = '{"category": "Computers and accessories", "keywords": ["laptop"], "min_ram_gb": 16, "min_storage_gb": 512, "storage_type": "SSD", "max_price": 1000.0, "currency": "USD"}'
    response = client.post("/assistant/intent", json={"query": "I need a laptop for university, preferably with 16GB RAM and 512GB SSD, under $1000."})
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "demo_catalog"
    assert "intent" in data
    assert "matches" in data
    assert len(data["matches"]) >= 1
    # Ensure products come from catalog
    for match in data["matches"]:
        assert "id" in match["product"]
        assert match["product"]["currency"] == "USD"


@patch("main.generate_response")
def test_invalid_malformed_gemini_json(mock_gen):
    mock_gen.return_value = "not json at all"
    response = client.post("/assistant/intent", json={"query": "laptop"})
    assert response.status_code == 400


@patch("main.generate_response")
def test_missing_gemini_api_key(mock_gen):
    mock_gen.side_effect = ValueError("Gemini API key is not configured.")
    response = client.post("/assistant/intent", json={"query": "laptop"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Gemini API key is not configured."


@patch("main.generate_response")
def test_gemini_runtime_error_returns_exception_message(mock_gen):
    message = "Gemini API error 429: quota exceeded"
    mock_gen.side_effect = RuntimeError(message)
    response = client.post("/assistant/intent", json={"query": "laptop"})
    assert response.status_code == 502
    assert response.json()["detail"] == message


@patch("main.generate_response")
def test_unexpected_error_returns_only_exception_type(mock_gen):
    mock_gen.side_effect = Exception("GEMINI_API_KEY=do-not-leak")
    response = client.post("/assistant/intent", json={"query": "laptop"})
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail == "Unexpected error: Exception"
    assert "GEMINI_API_KEY" not in detail
    assert "do-not-leak" not in detail


@patch("main.generate_response")
def test_max_price_filtering(mock_gen):
    mock_gen.return_value = '{"category": "Computers and accessories", "keywords": ["laptop"], "max_price": 800.0}'
    response = client.post("/assistant/intent", json={"query": "cheap laptop"})
    assert response.status_code == 200
    data = response.json()
    for match in data["matches"]:
        assert match["product"]["price"] <= 800.0


@patch("main.generate_response")
def test_ram_and_storage_constraint_handling(mock_gen):
    mock_gen.return_value = '{"category": "Computers and accessories", "keywords": ["laptop"], "min_ram_gb": 32, "min_storage_gb": 1000, "storage_type": "SSD"}'
    response = client.post("/assistant/intent", json={"query": "powerful laptop"})
    assert response.status_code == 200
    data = response.json()
    # Gaming laptop has 32GB RAM and 1TB SSD
    assert any(m["product"]["id"] == "prod-023" for m in data["matches"])


@patch("main.generate_response")
def test_unknown_specifications_not_satisfied(mock_gen):
    mock_gen.return_value = '{"category": "Clothing", "keywords": ["shirt"], "min_ram_gb": 16}'
    response = client.post("/assistant/intent", json={"query": "shirt with ram"})
    assert response.status_code == 200
    data = response.json()
    # Products with no verifiable RAM cannot satisfy RAM requirement
    assert len(data["matches"]) == 0


@patch("main.generate_response")
def test_product_ranking(mock_gen):
    mock_gen.return_value = '{"category": "Computers and accessories", "keywords": ["laptop"], "min_ram_gb": 16, "min_storage_gb": 512, "storage_type": "SSD"}'
    response = client.post("/assistant/intent", json={"query": "laptop"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["matches"]) >= 1
    scores = [m["score"] for m in data["matches"]]
    assert scores == sorted(scores, reverse=True)
    assert "score" in data["matches"][0]
    assert "reasons" in data["matches"][0]


@patch("main.generate_response")
def test_gemini_cannot_inject_nonexistent_products(mock_gen):
    mock_gen.return_value = '{"category": "Computers and accessories", "keywords": ["laptop"], "matches": [{"product": {"id": "fake-123", "name": "Fake Laptop", "price": 1.0}}]}'
    response = client.post("/assistant/intent", json={"query": "laptop"})
    assert response.status_code == 200
    data = response.json()
    # Should only have real catalog products
    for match in data["matches"]:
        assert match["product"]["id"] not in ["fake-123"]
    # All products must exist in catalog
    from app import catalog
    all_ids = {p["id"] for p in catalog.get_all_products()}
    for match in data["matches"]:
        assert match["product"]["id"] in all_ids


@patch("main.get_all_products")
@patch("main.generate_response")
def test_brand_constraint_excludes_other_and_missing_brands(mock_gen, mock_products):
    mock_gen.return_value = '{"category": "Computers and accessories", "keywords": ["laptop"], "brand": "ultrabook"}'
    mock_products.return_value = [
        {
            "id": "brand-match",
            "name": "UltraBook Laptop",
            "category": "Computers and accessories",
            "description": "Demo laptop with 16GB RAM and 512GB SSD.",
            "price": 899.99,
            "currency": "USD",
            "brand": "UltraBook",
            "availability": "in_stock",
        },
        {
            "id": "brand-other",
            "name": "GameForge Laptop",
            "category": "Computers and accessories",
            "description": "Demo laptop with 16GB RAM and 512GB SSD.",
            "price": 899.99,
            "currency": "USD",
            "brand": "GameForge",
            "availability": "in_stock",
        },
        {
            "id": "brand-missing",
            "name": "Mystery Laptop",
            "category": "Computers and accessories",
            "description": "Demo laptop with 16GB RAM and 512GB SSD.",
            "price": 899.99,
            "currency": "USD",
            "availability": "in_stock",
        },
    ]
    response = client.post("/assistant/intent", json={"query": "laptop from ultrabook"})
    assert response.status_code == 200
    data = response.json()
    product_ids = [m["product"]["id"] for m in data["matches"]]
    assert product_ids == ["brand-match"]


@patch("main.generate_response")
def test_max_storage_enforces_storage_type_and_capacity(mock_gen):
    mock_gen.return_value = '{"category": "Computers and accessories", "keywords": ["laptop"], "max_storage_gb": 300, "storage_type": "SSD"}'
    response = client.post(
        "/assistant/intent",
        json={"query": "laptop with at most 300GB SSD"},
    )
    assert response.status_code == 200
    data = response.json()
    product_ids = [m["product"]["id"] for m in data["matches"]]
    assert product_ids == ["prod-024"]


@patch("main.generate_response")
def test_storage_type_mismatch_excluded_with_max_storage(mock_gen):
    mock_gen.return_value = '{"category": "Computers and accessories", "keywords": ["laptop"], "max_storage_gb": 2000, "storage_type": "HDD"}'
    response = client.post(
        "/assistant/intent",
        json={"query": "laptop with an HDD under 2000GB"},
    )
    assert response.status_code == 200
    assert response.json()["matches"] == []


@patch("main.generate_response")
def test_storage_type_mismatch_excluded_with_min_storage(mock_gen):
    mock_gen.return_value = '{"category": "Computers and accessories", "keywords": ["laptop"], "min_storage_gb": 1, "storage_type": "HDD"}'
    response = client.post(
        "/assistant/intent",
        json={"query": "laptop with an HDD"},
    )
    assert response.status_code == 200
    assert response.json()["matches"] == []
