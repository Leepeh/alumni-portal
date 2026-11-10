from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import Role, notify
from core.breadcrumbs import crumbs

from .models import Event, EventRegistration, EventStatus


def event_list(request):
    """Афиша: предстоящие и прошедшие мероприятия."""
    show_past = request.GET.get("past") == "1"
    events = Event.objects.select_related("status").exclude(status__code=EventStatus.PLANNED)
    now = timezone.now()
    if show_past:
        events = events.filter(start_at__lt=now).order_by("-start_at")
    else:
        events = events.filter(start_at__gte=now)
    page = Paginator(events, 6).get_page(request.GET.get("page"))
    return render(request, "events/list.html", {
        "page": page,
        "show_past": show_past,
        "crumbs": crumbs("Мероприятия"),
    })


def event_detail(request, pk):
    """Карточка мероприятия с кнопкой регистрации."""
    event = get_object_or_404(Event.objects.select_related("status"), pk=pk)
    is_registered = False
    profile = getattr(request.user, "alumni_profile", None) if request.user.is_authenticated else None
    if profile:
        is_registered = event.registrations.filter(profile=profile).exists()
    return render(request, "events/detail.html", {
        "event": event,
        "is_registered": is_registered,
        "crumbs": crumbs(("Мероприятия", "events:list"), event.title),
    })


@require_POST
@role_required(Role.ALUMNUS)
def register_for_event(request, pk):
    """Регистрация выпускника на мероприятие с контролем числа мест."""
    with transaction.atomic():
        # Блокируем строку мероприятия на время проверки мест, чтобы два
        # одновременных запроса не заняли одно и то же последнее место
        event = get_object_or_404(Event.objects.select_for_update(), pk=pk)
        profile = request.user.alumni_profile
        if not event.is_registration_open:
            messages.error(request, "Регистрация на это мероприятие закрыта.")
        elif event.registrations.filter(profile=profile).exists():
            messages.info(request, "Вы уже зарегистрированы на это мероприятие.")
        elif event.free_places() <= 0:
            messages.error(request, "Свободных мест нет.")
        else:
            EventRegistration.objects.create(event=event, profile=profile)
            notify(request.user, f"Вы зарегистрированы на мероприятие «{event.title}».",
                   reverse("events:detail", args=[event.pk]))
            messages.success(request, "Вы зарегистрированы на мероприятие.")
    return redirect("events:detail", pk=pk)


@require_POST
@role_required(Role.ALUMNUS)
def cancel_registration(request, pk):
    """Отмена регистрации на мероприятие."""
    deleted, _ = EventRegistration.objects.filter(
        event_id=pk, profile=request.user.alumni_profile).delete()
    if deleted:
        notify(request.user, "Регистрация на мероприятие отменена.",
               reverse("events:detail", args=[pk]))
        messages.success(request, "Регистрация отменена.")
    return redirect("events:detail", pk=pk)
