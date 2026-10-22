import json
import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from main.models import CalorieProfile, FoodEntry
from main.off import OpenFoodFactsError, get_by_barcode, search_cache_key, search_products

MEALS = ("breakfast", "lunch", "dinner", "snack")
ACTIVITY_FACTORS = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725}
GOAL_ADJUSTMENTS = {"lose_025": -275, "lose_05": -550, "maintain": 0, "gain_025": 275}


def _error(code, status=400, **extra):
    return JsonResponse({"error": code, **extra}, status=status)


def _json_body(request):
    try:
        return json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _today():
    return timezone.localdate()


def _selected_date(value):
    if not value:
        return _today()
    try:
        selected = date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("invalid_date")
    if selected > _today():
        raise ValueError("future_date")
    return selected


def _profile_for(user):
    profile, _ = CalorieProfile.objects.get_or_create(user=user)
    return profile


def _needs(profile, on_date=None):
    complete = bool(profile.sex and profile.birth_date and profile.height_cm and profile.weight_kg and profile.activity_level and profile.goal)
    if not complete:
        return {"complete": False, "bmr": None, "maintenance": None, "goal_kcal": None}
    today = on_date or _today()
    age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day))
    bmr = 10 * float(profile.weight_kg) + 6.25 * float(profile.height_cm) - 5 * age + (5 if profile.sex == "male" else -161)
    maintenance = bmr * ACTIVITY_FACTORS[profile.activity_level]
    target = max(1200, round(maintenance + GOAL_ADJUSTMENTS[profile.goal]))
    return {"complete": True, "age": age, "bmr": round(bmr), "maintenance": round(maintenance), "goal_kcal": target}


def _profile_json(profile):
    return {
        "sex": profile.sex or "",
        "birth_date": profile.birth_date.isoformat() if profile.birth_date else "",
        "height_cm": float(profile.height_cm) if profile.height_cm is not None else "",
        "weight_kg": float(profile.weight_kg) if profile.weight_kg is not None else "",
        "activity_level": profile.activity_level or "",
        "goal": profile.goal or "",
        **_needs(profile),
    }


def _entry_json(entry):
    return {
        "id": entry.pk,
        "date": entry.date.isoformat(),
        "meal": entry.meal,
        "name": entry.name,
        "brand": entry.brand,
        "off_code": entry.off_code,
        "grams": float(entry.grams),
        "kcal_100g": float(entry.kcal_100g),
        "kcal": round(entry.kcal, 1),
        "protein_100g": float(entry.protein_100g) if entry.protein_100g is not None else None,
        "carbs_100g": float(entry.carbs_100g) if entry.carbs_100g is not None else None,
        "fat_100g": float(entry.fat_100g) if entry.fat_100g is not None else None,
        "nutriscore": entry.nutriscore,
    }


def _summary(user, selected):
    entries = FoodEntry.objects.filter(user=user, date=selected)
    totals = {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for entry in entries:
        factor = float(entry.grams) / 100
        totals["kcal"] += float(entry.kcal_100g) * factor
        totals["protein"] += float(entry.protein_100g or 0) * factor
        totals["carbs"] += float(entry.carbs_100g or 0) * factor
        totals["fat"] += float(entry.fat_100g or 0) * factor
    needs = _needs(_profile_for(user))
    goal = needs["goal_kcal"]
    macro_targets = {
        "carbs": round(goal * 0.5 / 4, 1) if goal else None,
        "protein": round(goal * 0.2 / 4, 1) if goal else None,
        "fat": round(goal * 0.3 / 9, 1) if goal else None,
    }
    consumed = round(totals["kcal"], 1)
    return {
        "date": selected.isoformat(),
        "consumed_kcal": consumed,
        "goal_kcal": goal,
        "remaining_kcal": round(goal - consumed, 1) if goal is not None else None,
        "over_goal": bool(goal and consumed > goal),
        "macros": {
            key: {"consumed_g": round(totals[key], 1), "target_g": macro_targets[key]}
            for key in ("carbs", "protein", "fat")
        },
        "needs": needs,
    }


def _date_from_request(request, key="date"):
    try:
        return _selected_date(request.GET.get(key))
    except ValueError as error:
        return str(error)


def _number(value, name, minimum=None, maximum=None, nullable=False):
    if value in (None, "") and nullable:
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"invalid_{name}")
    if not result.is_finite() or (minimum is not None and result < minimum) or (maximum is not None and result > maximum):
        raise ValueError(f"invalid_{name}")
    return result


def _validated_entry_data(data, default_date=None):
    if not isinstance(data, dict):
        raise ValueError("invalid_payload")
    name = str(data.get("name") or "").strip()
    if not name or len(name) > 200:
        raise ValueError("invalid_name")
    brand = str(data.get("brand") or "").strip()
    off_code = str(data.get("off_code") or "").strip()
    if len(brand) > 160 or len(off_code) > 32:
        raise ValueError("invalid_product")
    meal = data.get("meal")
    if meal not in MEALS:
        raise ValueError("invalid_meal")
    try:
        selected = _selected_date(data.get("date") or (default_date.isoformat() if default_date else None))
    except ValueError as error:
        raise ValueError(str(error))
    return {
        "date": selected,
        "meal": meal,
        "name": name,
        "brand": brand,
        "off_code": off_code,
        "grams": _number(data.get("grams"), "grams", Decimal("1"), Decimal("5000")),
        "kcal_100g": _number(data.get("kcal_100g"), "kcal_100g", Decimal("0"), Decimal("900")),
        "protein_100g": _number(data.get("protein_100g"), "protein", Decimal("0"), Decimal("100"), True),
        "carbs_100g": _number(data.get("carbs_100g"), "carbs", Decimal("0"), Decimal("100"), True),
        "fat_100g": _number(data.get("fat_100g"), "fat", Decimal("0"), Decimal("100"), True),
        "nutriscore": str(data.get("nutriscore") or "").lower() if str(data.get("nutriscore") or "").lower() in "abcde" and len(str(data.get("nutriscore") or "")) == 1 else "",
    }


def _default_meal():
    hour = timezone.localtime().hour
    if 5 <= hour < 11:
        return "breakfast"
    if 11 <= hour < 16:
        return "lunch"
    if 16 <= hour < 22:
        return "dinner"
    return "snack"


@login_required(login_url="main:login")
def calorie_count(request):
    profile = _profile_for(request.user)
    return render(request, "calorie_count.html", {
        "calorie_user_name": request.user.first_name or request.user.username,
        "calorie_today": _today().isoformat(),
        "default_meal": _default_meal(),
        "greeting_period": "morning" if timezone.localtime().hour < 12 else ("afternoon" if timezone.localtime().hour < 18 else "evening"),
        "profile": profile,
    })


@login_required(login_url="main:login")
@require_GET
def search_food(request):
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return _error("query_too_short")
    if len(query) > 100:
        return _error("invalid_query")
    try:
        page = int(request.GET.get("page", "1"))
        if page < 1 or page > 100:
            raise ValueError
    except ValueError:
        return _error("invalid_page")
    if cache.get(search_cache_key(query, page)) is None:
        if not cache.add(f"off:user-throttle:{request.user.pk}", 1, timeout=2):
            return _error("slow_down", 429)
        minute_key = timezone.now().strftime("%Y%m%d%H%M")
        counter_key = f"off:global-throttle:{minute_key}"
        cache.add(counter_key, 0, timeout=120)
        count = cache.incr(counter_key)
        if count > 10:
            cache.decr(counter_key)
            return _error("slow_down", 429)
    try:
        results = search_products(query, page)
    except OpenFoodFactsError as error:
        if error.status == 429:
            return _error("slow_down", 429)
        return _error("upstream_unavailable", 502)
    return JsonResponse({"results": results, "page": page, "page_size": 10})


@login_required(login_url="main:login")
@require_GET
def barcode_food(request, code):
    if not re.fullmatch(r"\d{8,14}", code):
        return _error("invalid_barcode")
    try:
        product = get_by_barcode(code)
    except OpenFoodFactsError as error:
        if error.status == 429:
            return _error("slow_down", 429)
        return _error("upstream_unavailable", 502)
    if not product:
        return _error("product_not_found", 404)
    return JsonResponse({"result": product})


@login_required(login_url="main:login")
@require_GET
def entries_api(request):
    selected = _date_from_request(request)
    if isinstance(selected, str):
        return _error(selected)
    entries = list(FoodEntry.objects.filter(user=request.user, date=selected))
    totals = {meal: 0.0 for meal in MEALS}
    for entry in entries:
        totals[entry.meal] += entry.kcal
    return JsonResponse({
        "date": selected.isoformat(),
        "entries": [_entry_json(entry) for entry in entries],
        "meal_totals": {meal: round(value, 1) for meal, value in totals.items()},
    })


@login_required(login_url="main:login")
@require_http_methods(["GET", "POST"])
def entries_collection_api(request):
    if request.method == "GET":
        return entries_api(request)
    data = _json_body(request)
    if data is None:
        return _error("invalid_json")
    try:
        values = _validated_entry_data(data)
    except ValueError as error:
        return _error(str(error))
    entry = FoodEntry.objects.create(user=request.user, **values)
    return JsonResponse({"entry": _entry_json(entry), "summary": _summary(request.user, entry.date)}, status=201)


@login_required(login_url="main:login")
@require_http_methods(["PATCH", "DELETE"])
def entry_detail_api(request, entry_id):
    entry = get_object_or_404(FoodEntry, pk=entry_id, user=request.user)
    if request.method == "DELETE":
        payload = _entry_json(entry)
        entry.delete()
        return JsonResponse({"entry": payload, "deleted": True})
    data = _json_body(request)
    if data is None or not isinstance(data, dict):
        return _error("invalid_json")
    changed = False
    if "grams" in data:
        try:
            entry.grams = _number(data["grams"], "grams", Decimal("1"), Decimal("5000"))
        except ValueError as error:
            return _error(str(error))
        changed = True
    if "meal" in data:
        if data["meal"] not in MEALS:
            return _error("invalid_meal")
        entry.meal = data["meal"]
        changed = True
    if not changed:
        return _error("no_changes")
    entry.save(update_fields=["grams", "meal"])
    return JsonResponse({"entry": _entry_json(entry), "summary": _summary(request.user, entry.date)})


@login_required(login_url="main:login")
@require_GET
def summary_api(request):
    selected = _date_from_request(request)
    if isinstance(selected, str):
        return _error(selected)
    return JsonResponse(_summary(request.user, selected))


@login_required(login_url="main:login")
@require_GET
def week_summary_api(request):
    selected = _date_from_request(request, "end")
    if isinstance(selected, str):
        return _error(selected)
    needs = _needs(_profile_for(request.user))
    goal = needs["goal_kcal"]
    start = selected - timedelta(days=6)
    daily = {start + timedelta(days=i): 0.0 for i in range(7)}
    for entry in FoodEntry.objects.filter(user=request.user, date__range=(start, selected)):
        daily[entry.date] += entry.kcal
    return JsonResponse({
        "start": start.isoformat(), "end": selected.isoformat(), "goal_kcal": goal,
        "days": [{"date": day.isoformat(), "kcal": round(total, 1), "goal_kcal": goal} for day, total in daily.items()],
    })


@login_required(login_url="main:login")
@require_http_methods(["GET", "PUT"])
def profile_api(request):
    profile = _profile_for(request.user)
    if request.method == "GET":
        return JsonResponse(_profile_json(profile))
    data = _json_body(request)
    if not isinstance(data, dict):
        return _error("invalid_json")
    allowed = {"sex", "birth_date", "height_cm", "weight_kg", "activity_level", "goal"}
    unknown = set(data) - allowed
    if unknown:
        return _error("invalid_fields")
    sex = data.get("sex", profile.sex)
    activity = data.get("activity_level", profile.activity_level)
    goal = data.get("goal", profile.goal)
    if sex not in {"", "male", "female"}:
        return _error("invalid_sex")
    if activity not in {"", *ACTIVITY_FACTORS}:
        return _error("invalid_activity_level")
    if goal not in {"", *GOAL_ADJUSTMENTS}:
        return _error("invalid_goal")
    raw_birth_date = data.get("birth_date", profile.birth_date.isoformat() if profile.birth_date else "")
    try:
        birth_date = date.fromisoformat(raw_birth_date) if raw_birth_date else None
    except (TypeError, ValueError):
        return _error("invalid_birth_date")
    if birth_date and birth_date >= _today():
        return _error("invalid_birth_date")
    try:
        height = _number(data.get("height_cm", profile.height_cm), "height_cm", Decimal("50"), Decimal("260"), True)
        weight = _number(data.get("weight_kg", profile.weight_kg), "weight_kg", Decimal("20"), Decimal("500"), True)
    except ValueError as error:
        return _error(str(error))
    profile.sex = sex
    profile.birth_date = birth_date
    profile.height_cm = height
    profile.weight_kg = weight
    profile.activity_level = activity
    profile.goal = goal
    profile.save()
    return JsonResponse(_profile_json(profile))
