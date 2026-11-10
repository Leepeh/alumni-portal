from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from club.forms import ProfileForm
from club.models import AlumniProfile
from core.breadcrumbs import crumbs

from .decorators import role_required
from .forms import LoginForm, PasswordForm
from .models import Role

CABINET = ("Личный кабинет", "accounts:cabinet")


class LoginView(auth_views.LoginView):
    """Страница входа на портал."""

    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
    extra_context = {"crumbs": crumbs("Вход")}


class LogoutView(auth_views.LogoutView):
    """Выход из учётной записи (только методом POST)."""


class PasswordChangeView(auth_views.PasswordChangeView):
    """Смена пароля в личном кабинете."""

    template_name = "accounts/password.html"
    form_class = PasswordForm
    success_url = reverse_lazy("accounts:password")

    def get_context_data(self, **kwargs):
        return super().get_context_data(crumbs=crumbs(CABINET, "Смена пароля"), **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Пароль изменён.")
        return super().form_valid(form)


def _profile(user):
    """Профиль выпускника текущего пользователя или ошибка 404, если его нет."""
    return get_object_or_404(AlumniProfile, user=user)


@login_required
def cabinet(request):
    """Стартовая страница кабинета: у каждой роли своя."""
    user = request.user
    if user.is_admin:
        return redirect("panel:dashboard")
    if user.is_moderator:
        return redirect("moderation:home")
    profile = _profile(user)
    now = timezone.now()
    return render(request, "accounts/cabinet.html", {
        "profile": profile,
        "upcoming": profile.registrations.select_related("event").filter(
            event__start_at__gte=now)[:3],
        "responses_count": profile.responses.count(),
        "unread_count": user.notifications.filter(is_read=False).count(),
        "crumbs": crumbs("Личный кабинет"),
    })


@role_required(Role.ALUMNUS)
def profile_edit(request):
    """Просмотр и изменение своего профиля, загрузка фотографии."""
    profile = _profile(request.user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Профиль сохранён.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {
        "form": form,
        "profile": profile,
        "crumbs": crumbs(CABINET, "Мой профиль"),
    })


@role_required(Role.ALUMNUS)
def my_events(request):
    """Мероприятия, на которые зарегистрирован выпускник."""
    registrations = _profile(request.user).registrations.select_related("event__status")
    now = timezone.now()
    return render(request, "accounts/my_events.html", {
        "upcoming": [r for r in registrations if r.event.start_at >= now],
        "past": [r for r in registrations if r.event.start_at < now],
        "crumbs": crumbs(CABINET, "Мои мероприятия"),
    })


@role_required(Role.ALUMNUS)
def my_responses(request):
    """Отклики выпускника на вакансии."""
    responses = _profile(request.user).responses.select_related("vacancy__partner")
    return render(request, "accounts/my_responses.html", {
        "responses": responses,
        "crumbs": crumbs(CABINET, "Мои отклики"),
    })


@login_required
def notifications(request):
    """Уведомления пользователя; при открытии страницы отмечаются прочитанными."""
    items = list(request.user.notifications.all()[:50])
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, "accounts/notifications.html", {
        "items": items,
        "crumbs": crumbs(CABINET, "Уведомления"),
    })


@role_required(Role.ALUMNUS)
def consents(request):
    """Согласия на обработку персональных данных и их отзыв."""
    return render(request, "accounts/consents.html", {
        "consents": request.user.consents.all(),
        "crumbs": crumbs(CABINET, "Согласия на обработку ПДн"),
    })


@require_POST
@role_required(Role.ALUMNUS)
def consent_revoke(request):
    """Отзыв согласия: учётная запись отключается, профиль скрывается из реестра."""
    user = request.user
    user.consents.filter(revoked_at__isnull=True).update(revoked_at=timezone.now())
    user.is_active = False
    user.save(update_fields=["is_active"])
    logout(request)
    messages.info(request, "Согласие отозвано. Учётная запись отключена, профиль скрыт "
                           "из реестра клуба.")
    return redirect("core:home")
