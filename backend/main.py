from decimal import Decimal
import json
import logging
import re

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, PrivateAttr

from app.catalog import get_all_products, get_product_by_id, search_products
from app.config import settings
from app.gemini import (
    GEMINI_FAILURE_MESSAGE,
    GEMINI_TIMEOUT_MESSAGE,
    GeminiTimeoutError,
    generate_response,
)
from app.paypal import (
    create_paypal_order,
    get_paypal_order,
    verify_paypal_approval,
    capture_paypal_order
)


logger = logging.getLogger(__name__)


app = FastAPI(
    title="CartPilot AI",
    description="Your Personal Autonomous Shopping Agent",
    version="1.0.0"
)


def _parse_cors_origins(value: str) -> list[str]:
    return [
        origin.strip()
        for origin in value.split(",")
        if origin.strip()
    ]


def _add_cors_middleware(target_app: FastAPI, origins: list[str]) -> None:
    target_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )


_add_cors_middleware(app, _parse_cors_origins(settings.cors_allow_origins))


class OrderRequest(BaseModel):
    amount: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2
    )


class IntentRequest(BaseModel):
    query: str = Field(min_length=1)


class ShoppingIntent(BaseModel):
    category: str | None = None
    keywords: list[str] = Field(default_factory=list)
    min_ram_gb: int | None = None
    max_ram_gb: int | None = None
    min_storage_gb: int | None = None
    max_storage_gb: int | None = None
    storage_type: str | None = None
    max_price: float | None = None
    min_price: float | None = None
    brand: str | None = None
    currency: str = "USD"
    use_case: str | None = None
    _primary_product_types: list[str] = PrivateAttr(default_factory=list)


@app.get("/")
async def root():
    return {
        "message": "Welcome to CartPilot AI",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "application": "CartPilot AI"
    }


@app.get("/products")
async def list_products(category: str | None = Query(default=None)):
    products = get_all_products()
    if category:
        category_lower = category.strip().lower()
        products = [
            product for product in products
            if product.get("category", "").lower() == category_lower
        ]
    return {
        "source": "demo_catalog",
        "count": len(products),
        "products": products
    }


@app.get("/products/search")
async def search_catalog(
    q: str = Query(min_length=1),
    category: str | None = Query(default=None),
    max_results: int = Query(default=10, ge=1, le=50)
):
    results = search_products(q, category=category, max_results=max_results)
    return {
        "source": "demo_catalog",
        "query": q,
        "count": len(results),
        "products": results
    }


@app.get("/products/{product_id}")
async def get_product(product_id: str):
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "source": "demo_catalog",
        "product": product
    }


def _extract_json_from_text(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    # Try to find JSON object
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


def _get_catalog_categories() -> set[str]:
    categories = set()
    for product in get_all_products():
        cat = product.get("category")
        if cat:
            categories.add(str(cat))
    return categories


_PRODUCT_TYPE_SYNONYMS = {
    "laptop": "laptop",
    "laptops": "laptop",
    "notebook": "laptop",
    "notebooks": "laptop",
    "smartphone": "smartphone",
    "smartphones": "smartphone",
    "smartphone camera": "smartphone",
    "smartphone cameras": "smartphone",
    "camera phone": "smartphone",
    "camera phones": "smartphone",
    "mobile phone": "smartphone",
    "mobile phones": "smartphone",
    "cell phone": "smartphone",
    "cell phones": "smartphone",
    "phone": "smartphone",
    "phones": "smartphone",
    "headphone": "headphones",
    "headphones": "headphones",
    "earbud": "earbuds",
    "earbuds": "earbuds",
    "earphone": "earbuds",
    "earphones": "earbuds",
    "speaker": "speaker",
    "speakers": "speaker",
    "camera": "camera",
    "cameras": "camera",
    "monitor": "monitor",
    "monitors": "monitor",
    "keyboard": "keyboard",
    "keyboards": "keyboard",
    "mouse": "mouse",
    "mice": "mouse",
    "usb hub": "hub",
    "usb-c hub": "hub",
    "hub": "hub",
    "hubs": "hub",
    "charger": "charger",
    "chargers": "charger",
    "charging pad": "charger",
    "smartphone charger": "charger",
    "smartphone chargers": "charger",
    "mobile phone charger": "charger",
    "mobile phone chargers": "charger",
    "phone charger": "charger",
    "phone chargers": "charger",
    "laptop charger": "charger",
    "laptop chargers": "charger",
    "camera charger": "charger",
    "camera chargers": "charger",
    "chair": "chair",
    "chairs": "chair",
    "office chair": "chair",
    "office chairs": "chair",
    "desk chair": "chair",
    "desk chairs": "chair",
    "ergonomic chair": "chair",
    "ergonomic chairs": "chair",
    "gaming chair": "chair",
    "gaming chairs": "chair",
    "smartphone case": "case",
    "smartphone cases": "case",
    "smartphone camera case": "case",
    "smartphone camera cases": "case",
    "camera phone case": "case",
    "camera phone cases": "case",
    "mobile phone case": "case",
    "mobile phone cases": "case",
    "cell phone case": "case",
    "cell phone cases": "case",
    "phone case": "case",
    "phone cases": "case",
    "laptop case": "case",
    "laptop cases": "case",
    "camera case": "case",
    "camera cases": "case",
    "case": "case",
    "cases": "case",
    "screen protector": "protector",
    "protector": "protector",
    "t-shirt": "t-shirt",
    "t-shirts": "t-shirt",
    "t shirt": "t-shirt",
    "t shirts": "t-shirt",
    "tshirt": "t-shirt",
    "tshirts": "t-shirt",
    "tee": "t-shirt",
    "tees": "t-shirt",
    "shirt": "shirt",
    "shirts": "shirt",
    "denim jeans": "jeans",
    "jeans": "jeans",
    "denim": "jeans",
    "hoodie": "hoodie",
    "hoodies": "hoodie",
    "hooded sweatshirt": "hoodie",
    "sweatshirt": "hoodie",
    "sweatshirts": "hoodie",
    "running shoes": "sneakers",
    "running shoe": "sneakers",
    "sneaker": "sneakers",
    "sneakers": "sneakers",
    "shoe": "sneakers",
    "shoes": "sneakers",
    "mug": "mug",
    "mugs": "mug",
    "candle": "candle",
    "candles": "candle",
    "lamp": "lamp",
    "lamps": "lamp",
    "blanket": "blanket",
    "blankets": "blanket",
}


_PRODUCT_TYPE_NAME_PATTERNS = {
    "laptop": [r"\blaptops?\b", r"\bnotebooks?\b"],
    "smartphone": [r"\bsmartphones?\b", r"\bmobile phones?\b", r"\bcell ?phones?\b"],
    "headphones": [r"\bheadphones?\b", r"\bover-ear\b"],
    "earbuds": [r"\bearbuds?\b", r"\bearphones?\b"],
    "speaker": [r"\bspeakers?\b"],
    "camera": [r"\bcameras?\b"],
    "monitor": [r"\bmonitors?\b"],
    "keyboard": [r"\bkeyboards?\b"],
    "mouse": [r"\bmouse\b", r"\bmice\b"],
    "hub": [r"\bhub\b", r"\bhubs\b"],
    "charger": [r"\bchargers?\b"],
    "chair": [r"\bchairs?\b"],
    "case": [r"\bcases?\b"],
    "protector": [r"\bprotectors?\b", r"\bscreen protector\b"],
    "t-shirt": [r"\bt[- ]?shirts?\b", r"\btees?\b"],
    "shirt": [r"\bshirts?\b"],
    "jeans": [r"\bjeans\b", r"\bdenim\b"],
    "hoodie": [r"\bhoodies?\b", r"\bhooded\b", r"\bsweatshirts?\b"],
    "sneakers": [r"\bsneakers?\b", r"\bshoes?\b", r"\brunning shoes?\b"],
    "mug": [r"\bmugs?\b"],
    "candle": [r"\bcandles?\b"],
    "lamp": [r"\blamps?\b"],
    "blanket": [r"\bblankets?\b"],
}


_PRODUCT_TYPE_TO_CATEGORY = {
    "laptop": "Computers and accessories",
    "mouse": "Computers and accessories",
    "keyboard": "Computers and accessories",
    "monitor": "Computers and accessories",
    "hub": "Computers and accessories",
    "charger": "Mobile phones",
    "chair": "Home and lifestyle",
    "case": "Mobile phones",
    "protector": "Mobile phones",
    "smartphone": "Mobile phones",
    "headphones": "Electronics",
    "earbuds": "Electronics",
    "speaker": "Electronics",
    "camera": "Electronics",
    "t-shirt": "Clothing",
    "shirt": "Clothing",
    "jeans": "Clothing",
    "hoodie": "Clothing",
    "sneakers": "Clothing",
    "mug": "Home and lifestyle",
    "candle": "Home and lifestyle",
    "lamp": "Home and lifestyle",
    "blanket": "Home and lifestyle",
}


_CATEGORY_SYNONYMS = {
    "clothing": "Clothing",
    "clothes": "Clothing",
    "apparel": "Clothing",
    "fashion": "Clothing",
    "electronics": "Electronics",
    "electronic": "Electronics",
    "gadgets": "Electronics",
    "tech": "Electronics",
    "technology": "Electronics",
    "computers and accessories": "Computers and accessories",
    "computer accessories": "Computers and accessories",
    "computers": "Computers and accessories",
    "computer": "Computers and accessories",
    "mobile phones": "Mobile phones",
    "mobile phone": "Mobile phones",
    "home and lifestyle": "Home and lifestyle",
    "home essentials": "Home and lifestyle",
    "home": "Home and lifestyle",
    "lifestyle": "Home and lifestyle",
    "furniture": "Home and lifestyle",
}


def _find_product_type_mentions(text: str) -> list[tuple[int, int, str]]:
    text_lower = text.lower()
    candidates: list[tuple[int, int, str]] = []
    for phrase, product_type in _PRODUCT_TYPE_SYNONYMS.items():
        pattern = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
        for match in re.finditer(pattern, text_lower):
            candidates.append((match.start(), match.end(), product_type))
    # Prefer longer phrases so "phone case" is treated as a case, not a phone.
    candidates.sort(key=lambda item: (-(item[1] - item[0]), item[0]))
    accepted_mentions: list[tuple[int, int, str]] = []
    accepted_spans: list[tuple[int, int]] = []
    for start, end, product_type in candidates:
        overlaps = any(
            start < span_end and end > span_start
            for span_start, span_end in accepted_spans
        )
        if overlaps:
            continue
        accepted_spans.append((start, end))
        accepted_mentions.append((start, end, product_type))
    accepted_mentions.sort(key=lambda item: item[0])
    return accepted_mentions


def _find_product_types(text: str) -> list[str]:
    found_types: list[str] = []
    for _, _, product_type in _find_product_type_mentions(text):
        if product_type not in found_types:
            found_types.append(product_type)
    return found_types


_CLAUSE_BOUNDARY_PATTERN = re.compile(r"[,.;]|\band\b|\bor\b", re.IGNORECASE)
_FEATURE_PREFIX_PATTERN = re.compile(
    r"\b(?:with|for|has|having|featuring|includes|including|comes with|equipped with)\b",
    re.IGNORECASE,
)
_QUALITY_SUFFIX_PATTERN = re.compile(
    r"\b(?:good|great|excellent|quality|high[- ]resolution|better|best)\s*$",
    re.IGNORECASE,
)


def _is_descriptive_product_mention(
    text: str,
    start: int,
    has_primary_product: bool,
) -> bool:
    prefix = text[max(0, start - 60):start]
    clause_start = 0
    for match in _CLAUSE_BOUNDARY_PATTERN.finditer(prefix):
        clause_start = match.end()
    clause_prefix = prefix[clause_start:]

    if _FEATURE_PREFIX_PATTERN.search(clause_prefix):
        return True

    return (
        has_primary_product
        and clause_start == 0
        and bool(_QUALITY_SUFFIX_PATTERN.search(clause_prefix))
    )


def _select_primary_product_types(text: str) -> list[str]:
    selected: list[str] = []
    for start, _, product_type in _find_product_type_mentions(text):
        if product_type in selected:
            continue
        if _is_descriptive_product_mention(text, start, bool(selected)):
            continue
        selected.append(product_type)

    if not selected:
        mentions = _find_product_type_mentions(text)
        if mentions:
            selected.append(mentions[0][2])

    return selected


def _find_category(
    query: str,
    valid_categories: set[str],
    excluded_spans: list[tuple[int, int]] | None = None,
) -> str | None:
    query_lower = query.lower()
    excluded_spans = excluded_spans or []
    for phrase in sorted(_CATEGORY_SYNONYMS, key=len, reverse=True):
        category = _CATEGORY_SYNONYMS[phrase]
        if category not in valid_categories:
            continue
        pattern = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
        for match in re.finditer(pattern, query_lower):
            if any(
                match.start() < span_end and match.end() > span_start
                for span_start, span_end in excluded_spans
            ):
                continue
            return category
    return None


def _product_matches_types(product_name_lower: str, product_types: list[str]) -> bool:
    for product_type in product_types:
        for pattern in _PRODUCT_TYPE_NAME_PATTERNS.get(product_type, []):
            if re.search(pattern, product_name_lower):
                return True
    return False


def _get_categories_for_product_types(product_types: list[str]) -> set[str]:
    categories: set[str] = set()
    if not product_types:
        return categories

    for product in get_all_products():
        product_name_lower = str(product.get("name", "")).lower()
        if not _product_matches_types(product_name_lower, product_types):
            continue
        category = product.get("category")
        if category:
            categories.add(str(category))
    return categories


def _preserve_product_types(query: str, intent: ShoppingIntent) -> ShoppingIntent:
    found_types = _find_product_types(query)
    primary_types = _select_primary_product_types(query)
    intent._primary_product_types = primary_types

    if found_types:
        existing_keywords_lower = {k.lower() for k in intent.keywords if k}
        merged_keywords = list(intent.keywords)
        for product_type in found_types:
            if product_type.lower() not in existing_keywords_lower:
                merged_keywords.append(product_type)
                existing_keywords_lower.add(product_type.lower())
        intent.keywords = merged_keywords

    valid_categories = _get_catalog_categories()
    product_type_spans = [
        (start, end) for start, end, _ in _find_product_type_mentions(query)
    ]
    intent.category = None
    if primary_types:
        catalog_categories = _get_categories_for_product_types(primary_types)
        if len(catalog_categories) == 1:
            intent.category = catalog_categories.pop()
        elif len(catalog_categories) > 1:
            intent.category = _find_category(
                query, valid_categories, product_type_spans
            )
        else:
            static_categories = {
                _PRODUCT_TYPE_TO_CATEGORY[product_type]
                for product_type in primary_types
                if _PRODUCT_TYPE_TO_CATEGORY.get(product_type) in valid_categories
            }
            if len(static_categories) == 1:
                intent.category = static_categories.pop()
            else:
                intent.category = _find_category(
                    query, valid_categories, product_type_spans
                )
    else:
        intent.category = _find_category(
            query, valid_categories, product_type_spans
        )

    return intent


def _extract_ram_gb(description: str) -> int | None:
    match = re.search(r"(\d+)\s*GB\s*RAM", description, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def _extract_storage_gb(description: str) -> tuple[int | None, str | None]:
    # Look for patterns like 512GB SSD, 1TB SSD, 256 GB SSD
    match = re.search(r"(\d+(?:\.\d+)?)\s*(TB|GB)\s*(SSD|HDD)", description, re.IGNORECASE)
    if match:
        value = float(match.group(1))
        unit = match.group(2).upper()
        storage_type = match.group(3).upper()
        gb = int(value * 1024) if unit == "TB" else int(value)
        return gb, storage_type
    # Fallback: just GB SSD/HDD
    match2 = re.search(r"(\d+)\s*GB\s*(SSD|HDD)", description, re.IGNORECASE)
    if match2:
        try:
            return int(match2.group(1)), match2.group(2).upper()
        except ValueError:
            return None, match2.group(2).upper()
    return None, None


@app.post("/assistant/intent")
async def assistant_intent(request: IntentRequest):
    prompt = (
        "You are a shopping intent extractor. Extract only structured shopping requirements as JSON. "
        "Do not return product recommendations, product IDs, prices, availability, scores, or lists of products. "
        "Return a JSON object with fields: category (string or null), keywords (array of strings), "
        "min_ram_gb (number or null), max_ram_gb (number or null), min_storage_gb (number or null), "
        "max_storage_gb (number or null), storage_type (string or null), max_price (number or null), "
        "min_price (number or null), brand (string or null), currency (string, default USD), use_case (string or null). "
        "category must be one of \"Electronics\", \"Computers and accessories\", \"Mobile phones\", "
        "\"Clothing\", \"Home and lifestyle\", or null only if none applies. "
        "Identify the main purchasable product. Treat camera quality, microphone quality, comfort, "
        "lightweight, and programming as keywords or use_case, not as additional product types. "
        f"User query: {request.query}"
    )

    try:
        response_text = await generate_response(prompt)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except GeminiTimeoutError:
        logger.warning("assistant_intent_gemini_timeout")
        raise HTTPException(
            status_code=504,
            detail=GEMINI_TIMEOUT_MESSAGE,
        )
    except RuntimeError as error:
        logger.warning(
            "assistant_intent_gemini_failed exception=%s",
            type(error).__name__,
        )
        raise HTTPException(status_code=502, detail=GEMINI_FAILURE_MESSAGE)
    except Exception as error:
        logger.warning(
            "assistant_intent_unexpected_error exception=%s",
            type(error).__name__,
        )
        raise HTTPException(status_code=502, detail=GEMINI_FAILURE_MESSAGE)

    try:
        parsed_json = _extract_json_from_text(response_text)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Gemini response format.")

    try:
        intent = ShoppingIntent.model_validate(parsed_json)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid shopping intent structure.")

    valid_categories = _get_catalog_categories()
    if intent.category and intent.category not in valid_categories:
        intent.category = None

    intent = _preserve_product_types(request.query, intent)
    primary_types = getattr(intent, "_primary_product_types", []) or []

    non_primary_keywords = [
        keyword for keyword in intent.keywords
        if keyword and keyword.lower() not in primary_types
    ]
    max_possible_score = 0
    if primary_types:
        max_possible_score += 40
    if intent.category:
        max_possible_score += 20
    if intent.max_price is not None:
        max_possible_score += 15
    if intent.min_price is not None:
        max_possible_score += 5
    if intent.min_ram_gb is not None:
        max_possible_score += 20
    if intent.max_ram_gb is not None:
        max_possible_score += 10
    if intent.min_storage_gb is not None:
        max_possible_score += 20
    if intent.max_storage_gb is not None:
        max_possible_score += 10
    if non_primary_keywords:
        max_possible_score += 5
    if intent.brand:
        max_possible_score += 10

    products = get_all_products() if (primary_types or intent.category) else []
    matches = []

    for product in products:
        reasons = []
        score = 0
        meets_constraints = True

        product_name = str(product.get("name", ""))
        product_name_lower = product_name.lower()
        product_category = product.get("category")

        if primary_types:
            if not _product_matches_types(product_name_lower, primary_types):
                continue
            score += 40
            reasons.append("Matches product type")

        if intent.category:
            if product_category != intent.category:
                continue
            reasons.append("Matches category")
            score += 20

        if intent.max_price is not None:
            try:
                if float(product.get("price", float("inf"))) <= float(intent.max_price):
                    reasons.append("Under budget")
                    score += 15
                else:
                    meets_constraints = False
            except (TypeError, ValueError):
                meets_constraints = False

        if intent.min_price is not None:
            try:
                if float(product.get("price", 0)) >= float(intent.min_price):
                    score += 5
                else:
                    meets_constraints = False
            except (TypeError, ValueError):
                meets_constraints = False

        if intent.min_ram_gb is not None:
            ram_gb = _extract_ram_gb(str(product.get("description", "")))
            if ram_gb is None:
                meets_constraints = False
            else:
                if ram_gb >= int(intent.min_ram_gb):
                    reasons.append("Meets RAM requirement")
                    score += 20
                else:
                    meets_constraints = False

        if intent.max_ram_gb is not None:
            ram_gb = _extract_ram_gb(str(product.get("description", "")))
            if ram_gb is None:
                meets_constraints = False
            else:
                if ram_gb <= int(intent.max_ram_gb):
                    score += 10
                else:
                    meets_constraints = False

        if intent.min_storage_gb is not None:
            storage_gb, storage_type = _extract_storage_gb(str(product.get("description", "")))
            if storage_gb is None:
                meets_constraints = False
            else:
                if intent.storage_type and storage_type != intent.storage_type.upper():
                    meets_constraints = False
                elif storage_gb >= int(intent.min_storage_gb):
                    reasons.append("Meets storage requirement")
                    score += 20
                else:
                    meets_constraints = False

        if intent.max_storage_gb is not None:
            storage_gb, storage_type = _extract_storage_gb(str(product.get("description", "")))
            if storage_gb is None:
                meets_constraints = False
            else:
                if intent.storage_type and storage_type != intent.storage_type.upper():
                    meets_constraints = False
                elif storage_gb <= int(intent.max_storage_gb):
                    score += 10
                else:
                    meets_constraints = False

        if intent.keywords:
            name_lower = product_name_lower
            desc_lower = str(product.get("description", "")).lower()
            for keyword in intent.keywords:
                if keyword and keyword.lower() in primary_types:
                    continue
                if keyword and (keyword.lower() in name_lower or keyword.lower() in desc_lower):
                    reasons.append(f"Matches keyword: {keyword}")
                    score += 5
                    break

        if intent.brand:
            product_brand = product.get("brand")
            if product_brand and str(product_brand).strip().lower() == intent.brand.strip().lower():
                reasons.append("Matches brand")
                score += 10
            else:
                meets_constraints = False

        if not meets_constraints:
            continue

        if not reasons:
            reasons.append("Matches search criteria")

        matches.append({
            "product": dict(product),
            "score": score,
            "reasons": reasons
        })

    matches.sort(key=lambda x: x["score"], reverse=True)

    if max_possible_score > 0:
        for match in matches:
            match["score"] = min(
                100,
                int(round(match["score"] * 100 / max_possible_score))
            )

    return {
        "source": "demo_catalog",
        "query": request.query,
        "intent": intent.model_dump(),
        "matches": matches,
        "count": len(matches)
    }


@app.post("/paypal/orders")
async def create_order(request: OrderRequest):
    try:
        order = create_paypal_order(
            amount=f"{request.amount:.2f}",
            currency="USD"
        )

        approval_url = next(
            (
                link["href"]
                for link in order["links"]
                if link.get("rel") in ("approve", "payer-action", "payment")
            ),
            None
        )

        if not approval_url:
            raise ValueError("PayPal approval URL not found")

        return {
            "id": order["id"],
            "status": order["status"],
            "approval_url": approval_url
        }

    except RuntimeError as error:
        raise HTTPException(
           status_code=502,
           detail=str(error)
       )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unexpected error while creating PayPal Sandbox order."
        )


@app.get("/paypal/orders/{order_id}")
async def retrieve_order(order_id: str):
    try:
        return get_paypal_order(order_id)

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve PayPal order."
        )


@app.get("/paypal/orders/{order_id}/approval")
async def verify_order_approval(order_id: str):
    try:
        return verify_paypal_approval(order_id)

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unable to verify PayPal order approval."
        )


@app.post("/paypal/orders/{order_id}/capture")
async def capture_order(order_id: str):
    try:
        return capture_paypal_order(order_id)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unable to capture PayPal Sandbox order."
        )


from fastapi.responses import RedirectResponse


@app.get("/paypal/return")
async def paypal_return(token: str | None = None):
    from app.config import settings

    if not token:
        raise HTTPException(status_code=400, detail="PayPal returned without an order token.")

    base_url = getattr(settings, "frontend_return_url", "http://localhost:5173/?paypal=return")
    if "?" in base_url:
        redirect_url = f"{base_url}&token={token}"
    else:
        redirect_url = f"{base_url}?token={token}"
    return RedirectResponse(url=redirect_url, status_code=302)


@app.get("/paypal/cancel")
async def paypal_cancel():
    from app.config import settings

    base_url = getattr(settings, "frontend_cancel_url", "http://localhost:5173/?paypal=cancel")
    return RedirectResponse(url=base_url, status_code=302)