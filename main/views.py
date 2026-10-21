from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render, get_object_or_404
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST

from main.forms import ReviewsForm
from main.models import Reviews

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
def add_review_ajax(request):
    form = ReviewsForm(request.POST)
    if form.is_valid():
        review = form.save()
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