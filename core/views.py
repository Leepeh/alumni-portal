from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.utils._os import safe_join
from django.utils import timezone

from club.models import CONSENT_VERSION, AlumniProfile
from events.models import Event, EventStatus
from news.models import News, NewsCategory
from vacancies.models import Partner, Vacancy

from .breadcrumbs import crumbs
from .models import ClubDocument, GalleryPhoto


def home(request):
    """Главная страница: показатели клуба, ближайшие мероприятия, новости, истории."""
    now = timezone.now()
    stats = {
        "members": AlumniProfile.objects.count(),
        "events": Event.objects.filter(start_at__year=now.year).exclude(
            status__code__in=[EventStatus.PLANNED, EventStatus.CANCELLED]).count(),
        "partners": Partner.objects.count(),
        "vacancies": Vacancy.objects.count(),
    }
    upcoming = Event.objects.select_related("status").filter(
        start_at__gte=now, status__code=EventStatus.OPEN)[:3]
    latest_news = News.published.filter(category__code=NewsCategory.NEWS)[:3]
    stories = News.published.filter(category__code=NewsCategory.STORY)[:2]
    return render(request, "core/home.html", {
        "stats": stats,
        "upcoming": upcoming,
        "latest_news": latest_news,
        "stories": stories,
        "crumbs": [],
    })


def about(request):
    """Страница «О клубе»: цели, направления работы, порядок вступления."""
    return render(request, "core/about.html", {"crumbs": crumbs("О клубе")})


def gallery(request):
    """Фотогалерея мероприятий клуба."""
    page = Paginator(GalleryPhoto.objects.all(), 12).get_page(request.GET.get("page"))
    return render(request, "core/gallery.html", {"page": page, "crumbs": crumbs("Галерея")})


def documents(request):
    """Документы клуба для скачивания."""
    return render(request, "core/documents.html", {
        "documents": ClubDocument.objects.all(),
        "crumbs": crumbs("Документы"),
    })


def privacy(request):
    """Политика обработки персональных данных на портале."""
    return render(request, "core/privacy.html", {
        "consent_version": CONSENT_VERSION,
        "crumbs": crumbs(("Документы", "core:documents"), "Политика обработки персональных данных"),
    })


def media(request, path):
    """Отдаёт загруженные файлы. Резюме доступны только автору отклика и сотрудникам."""
    if path.startswith("resumes/"):
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied
        is_owner = user.is_alumnus and user.alumni_profile.responses.filter(
            resume_file=path).exists()
        if not (user.is_moderator or is_owner):
            raise PermissionDenied
    try:
        return FileResponse(open(safe_join(settings.MEDIA_ROOT, path), "rb"))
    except (OSError, ValueError):
        raise Http404("Файл не найден")


def permission_denied(request, exception=None):
    """Страница ошибки 403 с общим оформлением портала."""
    return render(request, "403.html", {"crumbs": crumbs("Доступ запрещён")}, status=403)


def page_not_found(request, exception=None):
    """Страница ошибки 404 с общим оформлением портала."""
    return render(request, "404.html", {"crumbs": crumbs("Страница не найдена")}, status=404)
