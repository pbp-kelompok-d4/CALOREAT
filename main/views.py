from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render

from main.models import Reviews

# Menampilkan main.
def show_main(request):
    context = {
        'review_list': Reviews.objects.order_by('-date')[:9],
    }
    return render(request, "index.html", context)
