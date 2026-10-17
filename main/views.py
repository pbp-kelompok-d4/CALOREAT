from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render

from main.forms import RegisterForm
import datetime

# Menampilkan main.
def show_main(request):
    return render(request, "index.html")

def register(request):
    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")

    context = {
        "name": "",
        "form": form,
    }
    return render(request, "register.html", context)

# BELUM SELESAI
def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        response = redirect("main:show_main")
        response.set_cookie('last_login', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return response

    context = {
        "name": "",
        "form": form,
    }
    return render(request, "login.html", context)

# BELUM SELESAI 
def logout_user(request):
    logout(request)
    
    response = redirect("main:show_main")
    response.delete_cookie('last_login')
    return response