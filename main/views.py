from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render, get_object_or_404
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test

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
    reviews = Reviews.objects.order_by('-date')[:6]
    data = [
        {
            "id": str(review.id),
            "customer_name": review.customer_name,
            "star": review.star,
            "content": review.content,
            "profile_picture": review.profile_picture,
            "date": review.date.strftime("%d %b %Y"),
        }
        for review in reviews
    ]
    return JsonResponse(data, safe=False)

# Add new reviews using AJAX
@require_POST
@login_required(login_url="/login/")
def add_review_ajax(request):
    form = ReviewsForm(request.POST)
    if form.is_valid():
        review = form.save()

        if request.user.is_authenticated:
            review.customer_name = request.user.first_name
        else:
            review.customer_name = "Guest"
            
        review.save()

        return JsonResponse({
            "status": "success",
            "message": "Review berhasil ditambahkan!",
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
@user_passes_test(lambda user: user.is_superuser, login_url="/login/")
def delete_review_ajax(request, id):
    review = get_object_or_404(Reviews, id=id)
    review.delete()
    return JsonResponse({
        "status": "success",
        "message": "Review berhasil dihapus!"
    })

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

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        if not form.cleaned_data["remember_me"]:
            request.session.set_expiry(0)
        return redirect("main:show_main")

    return render(request, "authentication.html", _auth_context("login", login_form=form))


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
