from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("gallery/", views.gallery, name="gallery"),
    path("documents/", views.documents, name="documents"),
    path("documents/privacy/", views.privacy, name="privacy"),
    path("healthz/", views.health, name="health"),
]
