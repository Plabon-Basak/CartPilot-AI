from typing import Any


_DEMO_CATALOG: list[dict[str, Any]] = [
    {
        "id": "prod-001",
        "name": "Wireless Noise Cancelling Headphones",
        "category": "Electronics",
        "description": "Over-ear headphones with active noise cancellation and 30-hour battery life.",
        "price": 199.99,
        "currency": "USD",
        "brand": "SoundWave",
        "availability": "in_stock",
    },
    {
        "id": "prod-002",
        "name": "True Wireless Earbuds",
        "category": "Electronics",
        "description": "Compact earbuds with touch controls and sweat resistance.",
        "price": 89.49,
        "currency": "USD",
        "brand": "AudioPulse",
        "availability": "in_stock",
    },
    {
        "id": "prod-003",
        "name": "Bluetooth Speaker Mini",
        "category": "Electronics",
        "description": "Portable speaker with rich sound and water-resistant design.",
        "price": 49.95,
        "currency": "USD",
        "brand": "BoomBox",
        "availability": "in_stock",
    },
    {
        "id": "prod-004",
        "name": "4K Action Camera",
        "category": "Electronics",
        "description": "Compact action camera for recording adventures in 4K resolution.",
        "price": 149.00,
        "currency": "USD",
        "brand": "AdventureCam",
        "availability": "in_stock",
    },
    {
        "id": "prod-005",
        "name": "USB-C Multiport Hub",
        "category": "Computers and accessories",
        "description": "Expand ports with HDMI, USB-A, and SD card reader for laptops.",
        "price": 39.99,
        "currency": "USD",
        "brand": "ConnectPro",
        "availability": "in_stock",
    },
    {
        "id": "prod-006",
        "name": "Mechanical Keyboard",
        "category": "Computers and accessories",
        "description": "Tactile mechanical keyboard with customizable backlighting.",
        "price": 79.99,
        "currency": "USD",
        "brand": "KeyForge",
        "availability": "in_stock",
    },
    {
        "id": "prod-007",
        "name": "Wireless Ergonomic Mouse",
        "category": "Computers and accessories",
        "description": "Ergonomic mouse designed for all-day comfort and precision.",
        "price": 59.49,
        "currency": "USD",
        "brand": "ErgoTech",
        "availability": "in_stock",
    },
    {
        "id": "prod-008",
        "name": "27-inch Monitor",
        "category": "Computers and accessories",
        "description": "Full HD IPS monitor with vibrant colors and slim bezels.",
        "price": 229.99,
        "currency": "USD",
        "brand": "ViewPlus",
        "availability": "in_stock",
    },
    {
        "id": "prod-009",
        "name": "Smartphone 128GB",
        "category": "Mobile phones",
        "description": "Unlocked smartphone with high-resolution display and long battery life.",
        "price": 699.00,
        "currency": "USD",
        "brand": "NovaMobile",
        "availability": "in_stock",
    },
    {
        "id": "prod-010",
        "name": "Phone Case Clear",
        "category": "Mobile phones",
        "description": "Slim transparent case with shock-absorbing corners.",
        "price": 19.99,
        "currency": "USD",
        "brand": "ShieldMate",
        "availability": "in_stock",
    },
    {
        "id": "prod-011",
        "name": "Magnetic Wireless Charger",
        "category": "Mobile phones",
        "description": "Fast wireless charging pad compatible with magnetic phone mounts.",
        "price": 34.49,
        "currency": "USD",
        "brand": "ChargeLink",
        "availability": "in_stock",
    },
    {
        "id": "prod-012",
        "name": "Screen Protector",
        "category": "Mobile phones",
        "description": "Tempered glass screen protector with high clarity and easy installation.",
        "price": 12.99,
        "currency": "USD",
        "brand": "ShieldMate",
        "availability": "in_stock",
    },
    {
        "id": "prod-013",
        "name": "Cotton T-Shirt",
        "category": "Clothing",
        "description": "Classic crew neck t-shirt made from soft cotton fabric.",
        "price": 24.99,
        "currency": "USD",
        "brand": "UrbanThread",
        "availability": "in_stock",
    },
    {
        "id": "prod-014",
        "name": "Denim Jeans",
        "category": "Clothing",
        "description": "Slim fit denim jeans with durable stitching for everyday wear.",
        "price": 59.99,
        "currency": "USD",
        "brand": "UrbanThread",
        "availability": "in_stock",
    },
    {
        "id": "prod-015",
        "name": "Hooded Sweatshirt",
        "category": "Clothing",
        "description": "Cozy hoodie with adjustable drawstring and front pocket.",
        "price": 49.99,
        "currency": "USD",
        "brand": "UrbanThread",
        "availability": "in_stock",
    },
    {
        "id": "prod-016",
        "name": "Running Sneakers",
        "category": "Clothing",
        "description": "Lightweight sneakers designed for running and casual wear.",
        "price": 79.99,
        "currency": "USD",
        "brand": "FitStride",
        "availability": "in_stock",
    },
    {
        "id": "prod-017",
        "name": "Ceramic Mug Set",
        "category": "Home and lifestyle",
        "description": "Set of four ceramic mugs perfect for coffee or tea.",
        "price": 29.99,
        "currency": "USD",
        "brand": "HomeEssence",
        "availability": "in_stock",
    },
    {
        "id": "prod-018",
        "name": "Scented Candle",
        "category": "Home and lifestyle",
        "description": "Relaxing scented candle with a clean burn for cozy spaces.",
        "price": 16.49,
        "currency": "USD",
        "brand": "HomeEssence",
        "availability": "in_stock",
    },
    {
        "id": "prod-019",
        "name": "Desk Lamp",
        "category": "Home and lifestyle",
        "description": "Adjustable LED desk lamp with multiple brightness levels.",
        "price": 39.49,
        "currency": "USD",
        "brand": "BrightNest",
        "availability": "in_stock",
    },
    {
        "id": "prod-020",
        "name": "Throw Blanket",
        "category": "Home and lifestyle",
        "description": "Soft woven throw blanket ideal for adding warmth to any room.",
        "price": 44.99,
        "currency": "USD",
        "brand": "CozyLane",
        "availability": "in_stock",
    },
    {
        "id": "prod-021",
        "name": "Wireless Charger Stand",
        "category": "Electronics",
        "description": "Vertical wireless charging stand for phones and earbuds.",
        "price": 39.99,
        "currency": "USD",
        "brand": "ChargeLink",
        "availability": "in_stock",
    },
    {
        "id": "prod-022",
        "name": "UltraBook Laptop 14-inch",
        "category": "Computers and accessories",
        "description": "Demo catalog laptop with Intel Core i7 processor, 16GB RAM, 512GB SSD, and sleek design for students and professionals.",
        "price": 899.99,
        "currency": "USD",
        "brand": "UltraBook",
        "availability": "in_stock",
    },
    {
        "id": "prod-023",
        "name": "Gaming Laptop 15.6-inch",
        "category": "Computers and accessories",
        "description": "Demo catalog gaming laptop with AMD Ryzen 7 processor, 32GB RAM, 1TB SSD, and dedicated graphics card for gaming.",
        "price": 1299.49,
        "currency": "USD",
        "brand": "GameForge",
        "availability": "in_stock",
    },
    {
        "id": "prod-024",
        "name": "Business Laptop 14-inch",
        "category": "Computers and accessories",
        "description": "Demo catalog business laptop with Intel Core i5 processor, 16GB RAM, 256GB SSD, and long battery life for work on the go.",
        "price": 749.99,
        "currency": "USD",
        "brand": "ProWork",
        "availability": "in_stock",
    },
    {
        "id": "prod-025",
        "name": "Convertible Laptop 13-inch",
        "category": "Computers and accessories",
        "description": "Demo catalog 2-in-1 convertible laptop with Intel Core i7 processor, 16GB RAM, 512GB SSD, and touch screen for versatile use.",
        "price": 949.49,
        "currency": "USD",
        "brand": "FlexLine",
        "availability": "in_stock",
    },
]


def get_all_products() -> list[dict[str, Any]]:
    return [dict(product) for product in _DEMO_CATALOG]


def get_product_by_id(product_id: str) -> dict[str, Any] | None:
    for product in _DEMO_CATALOG:
        if product.get("id") == product_id:
            return dict(product)
    return None


def search_products(query: str, category: str | None = None, max_results: int = 10) -> list[dict[str, Any]]:
    if not query or not query.strip():
        return []
    query_lower = query.strip().lower()
    name_matches: list[dict[str, Any]] = []
    other_matches: list[dict[str, Any]] = []
    for product in _DEMO_CATALOG:
        if category and product.get("category", "").lower() != category.strip().lower():
            continue
        name_text = str(product.get("name", "")).lower()
        if query_lower in name_text:
            name_matches.append(dict(product))
            continue
        searchable_text = " ".join(
            [
                str(product.get("category", "")),
                str(product.get("brand", "")),
                str(product.get("description", "")),
            ]
        ).lower()
        if query_lower in searchable_text:
            other_matches.append(dict(product))
    results = (name_matches + other_matches)[:max_results]
    return results
