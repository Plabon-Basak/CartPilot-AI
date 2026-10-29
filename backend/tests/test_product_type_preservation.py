from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


@patch("main.generate_response")
def test_laptop_for_university_preserves_laptop(mock_gen):
    mock_gen.return_value = '{"category": null, "keywords": ["university"], "min_ram_gb": 16, "min_storage_gb": 512, "storage_type": "SSD"}'
    response = client.post("/assistant/intent", json={"query": "I need a laptop for university, preferably with 16GB RAM and 512GB SSD, under $1000."})
    assert response.status_code == 200
    data = response.json()
    assert "laptop" in [k.lower() for k in data["intent"]["keywords"]]
    assert len(data["matches"]) >= 1


@patch("main.generate_response")
def test_smartphone_preserves_case_insensitive(mock_gen):
    mock_gen.return_value = '{"category": null, "keywords": []}'
    response = client.post("/assistant/intent", json={"query": "SMARTPHONE under $500"})
    assert response.status_code == 200
    data = response.json()
    assert "smartphone" in [k.lower() for k in data["intent"]["keywords"]]


@patch("main.generate_response")
def test_headphones_preserved(mock_gen):
    mock_gen.return_value = '{"category": null, "keywords": ["studying"]}'
    response = client.post("/assistant/intent", json={"query": "headphones for studying"})
    assert response.status_code == 200
    data = response.json()
    assert "headphones" in [k.lower() for k in data["intent"]["keywords"]]


@patch("main.generate_response")
def test_existing_keywords_not_duplicated(mock_gen):
    mock_gen.return_value = '{"category": null, "keywords": ["laptop", "university"]}'
    response = client.post("/assistant/intent", json={"query": "laptop for university"})
    assert response.status_code == 200
    data = response.json()
    laptop_count = sum(1 for k in data["intent"]["keywords"] if k.lower() == "laptop")
    assert laptop_count == 1


@patch("main.generate_response")
def test_partial_word_no_false_positive(mock_gen):
    mock_gen.return_value = '{"category": null, "keywords": []}'
    response = client.post("/assistant/intent", json={"query": "laptopbag is not a product"})
    assert response.status_code == 200
    data = response.json()
    # "laptopbag" contains "laptop" but not as whole word
    assert "laptop" not in [k.lower() for k in data["intent"]["keywords"]]


@patch("main.generate_response")
def test_multiple_product_types_preserved(mock_gen):
    mock_gen.return_value = '{"category": null, "keywords": []}'
    response = client.post("/assistant/intent", json={"query": "I need a laptop and headphones"})
    assert response.status_code == 200
    data = response.json()
    keywords_lower = [k.lower() for k in data["intent"]["keywords"]]
    assert "laptop" in keywords_lower
    assert "headphones" in keywords_lower


@patch("main.generate_response")
def test_no_product_type_unchanged(mock_gen):
    mock_gen.return_value = '{"category": null, "keywords": ["university"]}'
    response = client.post("/assistant/intent", json={"query": "something for university"})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"]["keywords"] == ["university"]
