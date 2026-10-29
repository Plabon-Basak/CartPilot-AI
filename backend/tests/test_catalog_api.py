from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_list_products():
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "demo_catalog"
    assert "products" in data
    assert len(data["products"]) >= 20


def test_list_products_category_filter():
    response = client.get("/products?category=Electronics")
    assert response.status_code == 200
    data = response.json()
    assert all(p["category"] == "Electronics" for p in data["products"])


def test_search_products():
    response = client.get("/products/search?q=headphones")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "demo_catalog"
    assert data["count"] >= 1
    assert len(data["products"]) >= 1


def test_search_products_with_category():
    response = client.get("/products/search?q=mouse&category=Computers%20and%20accessories")
    assert response.status_code == 200
    data = response.json()
    for product in data["products"]:
        assert product["category"].lower() == "computers and accessories"


def test_search_products_case_insensitive():
    response = client.get("/products/search?q=SPEAKER")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1


def test_search_products_limit_validation():
    response = client.get("/products/search?q=a&max_results=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["products"]) <= 3


def test_search_products_missing_query():
    response = client.get("/products/search")
    assert response.status_code == 422


def test_get_product_by_id():
    response = client.get("/products/prod-001")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "demo_catalog"
    assert data["product"]["id"] == "prod-001"


def test_get_product_not_found():
    response = client.get("/products/prod-999")
    assert response.status_code == 404
