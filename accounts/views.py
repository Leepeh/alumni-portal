from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.breadcrumbs import crumbs

from .forms import LoginForm


class LoginView(auth_views.LoginView):
    """Страница входа на портал."""

    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
    extra_context = {"crumbs": crumbs("Вход")}


class LogoutView(auth_views.LogoutView):
    """Выход из учётной записи (только методом POST)."""


@login_required
def cabinet(request):
    """Стартовая страница личного кабинета."""
    return render(request, "accounts/cabinet.html", {"crumbs": crumbs("Личный кабинет")})
