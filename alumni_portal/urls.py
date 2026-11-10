from django.urls import include, path

from core import views as core_views

urlpatterns = [
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("club/", include("club.urls")),
    path("events/", include("events.urls")),
    path("", include("news.urls")),
    path("", include("vacancies.urls")),
    path("", include("feedback.urls")),
    path("moderation/", include("moderation.urls")),
    path("panel/", include("panel.urls")),
    path("reports/", include("reports.urls")),
    # Загруженные файлы отдаются через представление с проверкой прав
    path("media/<path:path>", core_views.media, name="media"),
]

handler403 = "core.views.permission_denied"
handler404 = "core.views.page_not_found"
