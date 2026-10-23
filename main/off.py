"""Small, cached Open Food Facts client for Caloreat."""
import json
import hashlib
import logging
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.cache import cache

logger = logging.getLogger(__name__)
BASE_URL = "https://world.openfoodfacts.org"
SEARCH_URL = "https://search.openfoodfacts.org/search"
USER_AGENT = "Caloreat/0.1 (contact: orrickhatmoko@gmail.com)"
FIELDS = "code,product_name,brands,image_front_small_url,serving_size,serving_quantity,nutriscore_grade,nutriments"
TIMEOUT = 6


class OpenFoodFactsError(Exception):
    def __init__(self, status=None):
        self.status = status
        super().__init__(f"Open Food Facts request failed{f' (HTTP {status})' if status else ''}")


def _number(value):
    try:
        number = float(value)
        return number if number >= 0 else None
    except (TypeError, ValueError):
        return None


def normalize(product):
    name = (product.get("product_name") or "").strip()
    if not name:
        return None
    nutriments = product.get("nutriments") or {}
    kcal = _number(nutriments.get("energy-kcal_100g"))
    if kcal is None:
        kj = _number(nutriments.get("energy-kj_100g"))
        kcal = round(kj / 4.184, 1) if kj is not None else None
    grade = (product.get("nutriscore_grade") or "").lower()
    brands = product.get("brands") or ""
    if isinstance(brands, list):
        brands = ", ".join(str(b) for b in brands)
    brand = str(brands).split(",")[0].strip()
    return {
        "code": str(product.get("code") or ""),
        "name": name,
        "brand": brand,
        "image": product.get("image_front_small_url") or "",
        "kcal_100g": kcal,
        "protein_100g": _number(nutriments.get("proteins_100g")),
        "carbs_100g": _number(nutriments.get("carbohydrates_100g")),
        "fat_100g": _number(nutriments.get("fat_100g")),
        "serving_g": _number(product.get("serving_quantity")),
        "nutriscore": grade if grade in {"a", "b", "c", "d", "e"} else "",
        "has_nutrition": kcal is not None,
    }


def _get_json(url, query=""):
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read())
    except HTTPError as error:
        logger.warning("Open Food Facts request failed (status=%s, query=%s)", error.code, query[:80])
        raise OpenFoodFactsError(error.code) from error
    except (URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
        logger.warning("Open Food Facts request failed (status=network, query=%s): %s", query[:80], error)
        raise OpenFoodFactsError() from error


def search_cache_key(query, page=1):
    query_hash = hashlib.sha256(query.casefold().strip().encode("utf-8")).hexdigest()
    return f"off:search:{query_hash}:{page}"


def search_products(query, page=1):
    key = search_cache_key(query, page)
    cached = cache.get(key)
    if cached is not None:
        return cached
    params = urlencode({
        "q": query,
        "page": page,
        "page_size": 10,
        "fields": FIELDS,
    })
    data = _get_json(f"{SEARCH_URL}?{params}", query)
    products = data.get("hits") if "hits" in data else data.get("products", [])
    results = [item for item in (normalize(product) for product in products) if item]
    cache.set(key, results, 60 * 60 * 24)
    return results


def get_by_barcode(code):
    code = code.strip()
    if not re.fullmatch(r"\d{8,14}", code):
        return None
    if len(code) == 12:
        code = "0" + code
    key = f"off:barcode:{code}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    params = urlencode({"fields": FIELDS})
    data = _get_json(f"{BASE_URL}/api/v2/product/{code}.json?{params}", code)
    product = normalize(data.get("product") or {}) if data.get("status") == 1 else None
    cache.set(key, product, 60 * 60 * 24)
    return product
