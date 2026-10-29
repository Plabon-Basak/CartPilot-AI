from app import catalog


def test_get_all_products_count():
    products = catalog.get_all_products()
    assert isinstance(products, list)
    assert len(products) >= 20


def test_get_product_by_id():
    product = catalog.get_product_by_id("prod-001")
    assert product is not None
    assert product["id"] == "prod-001"
    assert product["currency"] == "USD"
    assert "price" in product


def test_search_products_by_name():
    results = catalog.search_products("headphones")
    assert len(results) >= 1
    assert any(r["id"] == "prod-001" for r in results)


def test_search_products_case_insensitive():
    results = catalog.search_products("SPEAKER")
    assert len(results) >= 1


def test_search_products_by_category_filter():
    results = catalog.search_products("mouse", category="Computers and accessories")
    assert len(results) >= 1
    for r in results:
        assert r["category"].lower() == "computers and accessories"


def test_search_products_by_brand():
    results = catalog.search_products("UrbanThread")
    assert len(results) >= 2


def test_search_products_missing():
    results = catalog.search_products("nonexistentproductxyz")
    assert results == []


def test_get_product_by_id_missing():
    assert catalog.get_product_by_id("prod-999") is None


def test_search_products_limit():
    results = catalog.search_products("a", max_results=3)
    assert len(results) <= 3


def test_search_products_empty_query():
    assert catalog.search_products("") == []
    assert catalog.search_products("   ") == []


def test_search_laptop_name_priority():
    results = catalog.search_products("laptop")
    assert len(results) >= 4
    # Name matches should come first
    assert "laptop" in results[0]["name"].lower()
    laptop_ids = {"prod-022", "prod-023", "prod-024", "prod-025"}
    assert all(r["id"] in laptop_ids for r in results[:4])
