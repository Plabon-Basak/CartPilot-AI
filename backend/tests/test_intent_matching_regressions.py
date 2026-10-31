from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


@patch("main.generate_response")
def test_smartphone_camera_feature_does_not_match_action_camera(mock_gen):
    mock_gen.return_value = (
        '{"category": null, "keywords": ["smartphone", "good camera"], '
        '"max_price": 500.0, "currency": "USD", "use_case": "photography"}'
    )
    response = client.post(
        "/assistant/intent",
        json={"query": "Find a smartphone with a good camera under $500."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"]["category"] == "Mobile phones"
    assert data["count"] == 0
    assert "prod-004" not in [match["product"]["id"] for match in data["matches"]]


@patch("main.generate_response")
def test_smartphone_over_budget_returns_no_unrelated_products(mock_gen):
    mock_gen.return_value = (
        '{"category": null, "keywords": ["smartphone"], "max_price": 500.0}'
    )
    response = client.post(
        "/assistant/intent",
        json={"query": "smartphone under $500"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"]["category"] == "Mobile phones"
    assert data["count"] == 0


@patch("main.generate_response")
def test_office_chair_without_catalog_matches_returns_empty(mock_gen):
    mock_gen.return_value = (
        '{"category": null, "keywords": ["ergonomic", "office chair"], '
        '"max_price": 250.0, "currency": "USD", "use_case": "office work"}'
    )
    response = client.post(
        "/assistant/intent",
        json={"query": "I need an ergonomic office chair under $250."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"]["category"] == "Home and lifestyle"
    assert data["count"] == 0


@patch("main.generate_response")
def test_laptop_budget_search_returns_only_laptops(mock_gen):
    mock_gen.return_value = (
        '{"category": "Computers and accessories", "keywords": ["laptop", "programming"], '
        '"max_price": 800.0, "currency": "USD", "use_case": "programming"}'
    )
    response = client.post(
        "/assistant/intent",
        json={"query": "Find me a laptop under $800 for programming."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"]["category"] == "Computers and accessories"
    assert [match["product"]["id"] for match in data["matches"]] == ["prod-024"]
    assert all(match["product"]["price"] <= 800.0 for match in data["matches"])


@patch("main.generate_response")
def test_headphones_feature_terms_do_not_broaden_product_type(mock_gen):
    mock_gen.return_value = (
        '{"category": "Electronics", '
        '"keywords": ["wireless", "headphones", "online classes", "microphone quality", "comfort"], '
        '"max_price": 100.0, "currency": "USD", "use_case": "online classes"}'
    )
    response = client.post(
        "/assistant/intent",
        json={
            "query": (
                "I need wireless headphones for online classes. My budget is $100 "
                "and microphone quality and comfort matter."
            )
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"]["category"] == "Electronics"
    assert data["count"] == 0


@patch("main.generate_response")
def test_action_camera_query_still_matches_camera_product(mock_gen):
    mock_gen.return_value = (
        '{"category": null, "keywords": ["camera"], "max_price": 200.0}'
    )
    response = client.post(
        "/assistant/intent",
        json={"query": "4K action camera under $200"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"]["category"] == "Electronics"
    assert [match["product"]["id"] for match in data["matches"]] == ["prod-004"]


@patch("main.generate_response")
def test_no_product_or_category_anchor_returns_no_matches(mock_gen):
    mock_gen.return_value = (
        '{"category": null, "keywords": ["something"], "max_price": 250.0}'
    )
    response = client.post(
        "/assistant/intent",
        json={"query": "something under $250"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"]["category"] is None
    assert data["count"] == 0


@patch("main.generate_response")
def test_wireless_charger_keeps_cross_category_matches(mock_gen):
    mock_gen.return_value = (
        '{"category": "Mobile phones", "keywords": ["wireless", "charger"], "max_price": 100.0}'
    )
    response = client.post(
        "/assistant/intent",
        json={"query": "wireless charger under $100"},
    )
    assert response.status_code == 200
    data = response.json()
    product_ids = {match["product"]["id"] for match in data["matches"]}
    assert "prod-011" in product_ids
    assert "prod-021" in product_ids


@patch("main.generate_response")
def test_explicit_multi_product_query_matches_both_types(mock_gen):
    mock_gen.return_value = (
        '{"category": null, "keywords": ["laptop", "headphones"], "max_price": 1000.0}'
    )
    response = client.post(
        "/assistant/intent",
        json={"query": "I need a laptop and headphones under $1000"},
    )
    assert response.status_code == 200
    data = response.json()
    product_names = [match["product"]["name"].lower() for match in data["matches"]]
    assert any("laptop" in name for name in product_names)
    assert any("headphones" in name for name in product_names)


@patch("main.generate_response")
def test_smartphone_camera_compounds_resolve_to_smartphone(mock_gen):
    mock_gen.return_value = (
        '{"category": null, "keywords": ["camera"], "max_price": 500.0}'
    )
    for query in (
        "Best smartphone camera under $500",
        "camera phone under $500",
    ):
        response = client.post("/assistant/intent", json={"query": query})
        assert response.status_code == 200
        data = response.json()
        assert data["intent"]["category"] == "Mobile phones"
        assert data["count"] == 0
        assert "prod-004" not in {
            match["product"]["id"] for match in data["matches"]
        }


@patch("main.generate_response")
def test_smartphone_charger_returns_chargers_only(mock_gen):
    mock_gen.return_value = (
        '{"category": "Mobile phones", "keywords": ["smartphone", "charger"], '
        '"max_price": 100.0}'
    )
    response = client.post(
        "/assistant/intent",
        json={"query": "Smartphone charger under $100"},
    )
    assert response.status_code == 200
    data = response.json()
    product_ids = {match["product"]["id"] for match in data["matches"]}
    assert product_ids == {"prod-011", "prod-021"}
    assert "prod-009" not in product_ids


@patch("main.generate_response")
def test_mobile_phone_charger_preserves_cross_category_chargers(mock_gen):
    mock_gen.return_value = (
        '{"category": "Mobile phones", "keywords": ["mobile phone", "charger"], '
        '"max_price": 100.0}'
    )
    response = client.post(
        "/assistant/intent",
        json={"query": "Mobile phone charger under $100"},
    )
    assert response.status_code == 200
    data = response.json()
    product_ids = {match["product"]["id"] for match in data["matches"]}
    assert product_ids == {"prod-011", "prod-021"}
    assert "prod-009" not in product_ids


@patch("main.generate_response")
def test_quality_adjective_after_conjunction_keeps_second_product(mock_gen):
    mock_gen.return_value = (
        '{"category": null, "keywords": ["laptop", "camera"], "max_price": 2000.0}'
    )
    response = client.post(
        "/assistant/intent",
        json={"query": "Best laptop and best camera under $2000"},
    )
    assert response.status_code == 200
    data = response.json()
    product_ids = {match["product"]["id"] for match in data["matches"]}
    product_names = [match["product"]["name"].lower() for match in data["matches"]]
    assert "prod-004" in product_ids
    assert any("laptop" in name for name in product_names)


@patch("main.generate_response")
def test_price_only_query_requires_grounded_category(mock_gen):
    mock_gen.return_value = (
        '{"category": "Electronics", "keywords": [], "max_price": 100.0}'
    )
    response = client.post(
        "/assistant/intent",
        json={"query": "under $100"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"]["category"] is None
    assert data["count"] == 0

    mock_gen.return_value = '{"category": null, "keywords": [], "max_price": 100.0}'
    response = client.post(
        "/assistant/intent",
        json={"query": "electronics under $100"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"]["category"] == "Electronics"
    assert data["count"] > 0


@patch("main.generate_response")
def test_accessory_compounds_do_not_recommend_parent_devices(mock_gen):
    mock_gen.return_value = '{"category": null, "keywords": ["case"]}'
    for query in (
        "phone case",
        "smartphone case",
        "laptop case",
        "camera case",
        "camera phone case",
        "smartphone camera case",
    ):
        response = client.post("/assistant/intent", json={"query": query})
        assert response.status_code == 200
        data = response.json()
        product_ids = {match["product"]["id"] for match in data["matches"]}
        assert data["intent"]["category"] == "Mobile phones"
        assert data["count"] == 1
        assert product_ids == {"prod-010"}
