from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


@patch("main.generate_response")
def test_best_denim_jeans_excludes_unrelated_clothing(mock_gen):
    mock_gen.return_value = '{"category": null, "keywords": []}'
    response = client.post("/assistant/intent", json={"query": "i need best denim jeans"})
    assert response.status_code == 200
    data = response.json()
    product_ids = [m["product"]["id"] for m in data["matches"]]
    assert product_ids == ["prod-014"]
    assert data["intent"]["category"] == "Clothing"


@patch("main.generate_response")
def test_jeans_prioritizes_jeans_products(mock_gen):
    mock_gen.return_value = '{"category": null, "keywords": []}'
    response = client.post("/assistant/intent", json={"query": "jeans"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["matches"]) >= 1
    assert data["matches"][0]["product"]["id"] == "prod-014"
    assert data["matches"][0]["score"] == 100


@patch("main.generate_response")
def test_best_laptop_excludes_unrelated_accessories(mock_gen):
    mock_gen.return_value = '{"category": null, "keywords": []}'
    response = client.post("/assistant/intent", json={"query": "best laptop"})
    assert response.status_code == 200
    data = response.json()
    product_ids = [m["product"]["id"] for m in data["matches"]]
    assert all(pid in ["prod-022", "prod-023", "prod-024", "prod-025"] for pid in product_ids)
    assert "prod-006" not in product_ids
    assert "prod-007" not in product_ids


@patch("main.generate_response")
def test_running_shoes_under_100_excludes_other_types(mock_gen):
    mock_gen.return_value = '{"category": null, "keywords": [], "max_price": 100.0}'
    response = client.post("/assistant/intent", json={"query": "running shoes under $100"})
    assert response.status_code == 200
    data = response.json()
    product_ids = [m["product"]["id"] for m in data["matches"]]
    assert product_ids == ["prod-016"]
    for match in data["matches"]:
        assert match["product"]["price"] <= 100.0
        assert match["score"] == 100


@patch("main.generate_response")
def test_best_clothing_allows_multiple_types(mock_gen):
    mock_gen.return_value = '{"category": null, "keywords": []}'
    response = client.post("/assistant/intent", json={"query": "best clothing"})
    assert response.status_code == 200
    data = response.json()
    product_ids = [m["product"]["id"] for m in data["matches"]]
    assert product_ids == ["prod-013", "prod-014", "prod-015", "prod-016"]
    assert data["intent"]["category"] == "Clothing"
    for match in data["matches"]:
        assert match["product"]["category"] == "Clothing"


@patch("main.generate_response")
def test_scores_are_normalized_percentages(mock_gen):
    mock_gen.return_value = '{"category": null, "keywords": ["gaming"]}'
    response = client.post("/assistant/intent", json={"query": "best laptop"})
    assert response.status_code == 200
    scores = [match["score"] for match in response.json()["matches"]]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= score <= 100 for score in scores)
    assert scores[0] == 100
    assert any(score < 100 for score in scores)
