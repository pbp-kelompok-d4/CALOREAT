from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import login, logout
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, render

from main.forms import RegisterForm, LoginForm

# Menampilkan main.
def show_main(request):
    return render(request, "index.html")

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