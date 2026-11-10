from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("club/", include("club.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
