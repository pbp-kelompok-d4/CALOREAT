from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required

from main.models import Reviews

from main.forms import RegisterForm, LoginForm, ReviewsForm


# Menampilkan main.
def show_main(request):
    context = {
        'review_list': Reviews.objects.order_by('-date')[:6],
    }
    return render(request, "index.html", context)


# get reviews json using AJAX
def get_reviews_json(request):
    reviews = Reviews.objects.order_by('-date')
    star_filter = request.GET.get("star", "").strip()
    star_map = {
        "5": "★★★★★",
        "4": "★★★★☆",
        "3": "★★★☆☆",
        "2": "★★☆☆☆",
        "1": "★☆☆☆☆",
        "0": "☆☆☆☆☆",
    }
    if star_filter:
        reviews = reviews.filter(star=star_map.get(star_filter, star_filter))

    data = [
        {
            "id": str(review.id),
            "customer_name": review.customer_name,
            "star": review.star,
            "content": review.content,
            "profile_picture": review.profile_picture,
            "date": review.date.strftime("%d %b %Y"),
            "can_edit": request.user.is_authenticated
            and (request.user.is_superuser or review.created_by_id == request.user.id),
        }
        for review in reviews
    ]
    return JsonResponse(data, safe=False)

# Add new reviews using AJAX
@require_POST
@login_required(login_url="/login/")
def add_review_ajax(request):
    if Reviews.objects.filter(created_by=request.user).exists():
        return JsonResponse({
            "status": "error",
            "message": "You already have a review. Please delete it before adding another.",
        }, status=409)

    form = ReviewsForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.created_by = request.user

        review.customer_name = request.user.first_name or "Admin"
        review.save()

        return JsonResponse({
            "status": "success",
            "message": "Review added successfully!",
            "review": {
                "customer_name": review.customer_name,
                "star": review.star,
                "content": review.content,
                "profile_picture": review.profile_picture,
                "date": review.date.strftime("%d %b %Y"),
            }
        }, status=201)
    
    return JsonResponse({
        "status": "error",
        "errors": form.errors
    }, status=400)

# Delete reviews
@require_POST
@login_required(login_url="/login/")
def delete_review_ajax(request, id):
    review = get_object_or_404(Reviews, id=id)
    if not (request.user.is_superuser or review.created_by_id == request.user.id):
        return redirect("main:login")
    review.delete()
    return JsonResponse({
        "status": "success",
        "message": "Review deleted successfully!"
    })

# Edit reviews using AJAX
@require_http_methods(["GET", "POST"])
@login_required(login_url="/login/")
def edit_review(request, reviews_id):
    review = get_object_or_404(Reviews, pk=reviews_id)
    if not (request.user.is_superuser or review.created_by_id == request.user.id):
        return redirect("main:login")

    if request.method == "GET":
        return JsonResponse({
            "id": str(review.id),
            "customer_name": review.customer_name,
            "star": review.star,
            "content": review.content,
        })

    form = ReviewsForm(request.POST, instance=review)
    if form.is_valid():
        review = form.save()
        return JsonResponse({
            "status": "success",
            "message": "Review updated successfully!",
            "review": {
                "id": str(review.id),
                "customer_name": review.customer_name,
                "star": review.star,
                "content": review.content,
                "profile_picture": review.profile_picture,
                "date": review.date.strftime("%d %b %Y"),
            },
        })

    return JsonResponse({
        "status": "error",
        "errors": form.errors,
    }, status=400)

def _auth_context(active, login_form=None, register_form=None):
    if login_form is None:
        login_form = LoginForm(auto_id="login_%s")
    if register_form is None:
        register_form = RegisterForm(auto_id="register_%s")
    return {
        "active": active,
        "login_form": login_form,
        "register_form": register_form,
    }


def login_user(request):
    form = LoginForm(request, data=request.POST or None, auto_id="login_%s")

    next_url = request.POST.get("next") or request.GET.get("next", "")
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        if not form.cleaned_data["remember_me"]:
            request.session.set_expiry(0)
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return redirect(next_url)
        return redirect("main:show_main")

    context = _auth_context("login", login_form=form)
    context["next"] = next_url
    return render(request, "authentication.html", context)


def register(request):
    form = RegisterForm(request.POST or None, auto_id="register_%s")

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")

    return render(request, "authentication.html", _auth_context("register", register_form=form))

@require_POST
def logout_user(request):
    logout(request)
    return redirect("main:login")
