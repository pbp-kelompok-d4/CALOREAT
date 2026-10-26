import hashlib
import requests
from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import render

API_URL = "https://search.openfoodfacts.org/search"
USER_AGENT = "Caloreat/0.1 (contact: orrickhatmoko@gmail.com)"
PER_PAGE = 12

# Daftar vitamin dan mineral yang mau ditampilkan di panel detail.
# Kiri = nama di API, kanan = nama yang tampil ke pengguna.
VITAMIN = [
    ("vitamin-a", "Vit A"), ("vitamin-b1", "Vit B1"), ("vitamin-b2", "Vit B2"),
    ("vitamin-b6", "Vit B6"), ("vitamin-b12", "Vit B12"), ("vitamin-c", "Vit C"),
    ("vitamin-d", "Vit D"), ("vitamin-e", "Vit E"),
]
MINERAL = [
    ("calcium", "Kalsium"), ("iron", "Zat besi"), ("magnesium", "Magnesium"),
    ("potassium", "Kalium"), ("sodium", "Natrium"), ("zinc", "Zinc"),
    ("phosphorus", "Fosfor"),
]


def angka(nutriments, kunci):
    """Ambil angka dari nutriments. Kalau tidak ada atau bukan angka, hasilnya None."""
    try:
        return float(nutriments.get(kunci))
    except (TypeError, ValueError):
        return None


def mikro(nutriments, daftar):
    """Ubah vitamin/mineral dari gram (satuan API) jadi teks mg atau mcg."""
    hasil = []
    for kunci, label in daftar:
        v = angka(nutriments, f"{kunci}_100g")
        if v:
            mg = v * 1000
            if mg < 1:
                teks = f"{round(mg * 1000, 1)} mcg"   # nilai sangat kecil, pakai mcg
            else:
                teks = f"{round(mg, 1)} mg"
            hasil.append(f"{label} {teks}")
    return hasil


def ambil_dari_api(q, page):
    """Panggil Search-a-licious API Open Food Facts dan simpan hasilnya di cache selama 24 jam."""
    normalized_q = q.casefold().strip()
    query_hash = hashlib.sha256(normalized_q.encode("utf-8")).hexdigest()
    key = f"off:catalog:{query_hash}:{page}"
    data = cache.get(key)
    if data is None:
        search_query = q if q else 'countries_tags:"en:indonesia"'
        resp = requests.get(
            API_URL,
            params={
                "q": search_query,
                "page": page,
                "page_size": PER_PAGE,
                "fields": (
                    "code,product_name,brands,quantity,"
                    "image_front_small_url,nutriscore_grade,nutriments"
                ),
            },
            headers={
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        cache.set(key, data, 60 * 60 * 24)
    return data


def food_catalog(request):
    q = request.GET.get("q", "").strip()
    try:
        page = max(1, int(request.GET.get("page", 1)))
    except ValueError:
        page = 1

    error = False
    try:
        data = ambil_dari_api(q, page)
    except requests.RequestException:
        data = {"count": 0, "hits": []}
        error = True

    try:
        total = int(data.get("count", 0))
    except (TypeError, ValueError):
        total = 0

    # Paginator hanya dipakai untuk menghitung nomor halaman (1 2 3 ... 181 182 183).
    paginator = Paginator(range(total), PER_PAGE)
    page_obj = paginator.get_page(page)
    page_range = paginator.get_elided_page_range(
        page_obj.number, on_each_side=1, on_ends=3
    )

    products = data.get("hits") if "hits" in data else data.get("products", [])
    foods = []
    for p in products:
        nama = (p.get("product_name") or "").strip()
        if not nama:
            continue  # lewati produk yang belum punya nama
        n = p.get("nutriments") or {}
        brands = p.get("brands")
        if isinstance(brands, list):
            brands = ", ".join(str(b) for b in brands if b)
        grade = (p.get("nutriscore_grade") or "").upper()
        kcal = angka(n, "energy-kcal_100g")
        if kcal is None:
            kj = angka(n, "energy-kj_100g")
            kcal = round(kj / 4.184, 1) if kj is not None else None

        foods.append({
            "nama": nama,
            "merek": ", ".join(filter(None, [brands, p.get("quantity")])),
            "gambar": p.get("image_front_small_url"),
            "nutriscore": grade if grade in {"A", "B", "C", "D", "E"} else "",
            "kcal": kcal,
            "protein": angka(n, "proteins_100g"),
            "karbo": angka(n, "carbohydrates_100g"),
            "lemak": angka(n, "fat_100g"),
            "serat": angka(n, "fiber_100g"),
            "gula": angka(n, "sugars_100g"),
            "vitamin": mikro(n, VITAMIN),
            "mineral": mikro(n, MINERAL),
        })

    return render(request, "catalog.html", {
        "foods": foods,
        "page_obj": page_obj,
        "page_range": page_range,
        "total": total,
        "q": q,
        "error": error,
    })