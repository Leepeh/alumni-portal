from django.urls import path

from . import views

app_name = "club"

urlpatterns = [
    path("join/", views.join, name="join"),
    path("join/done/", views.join_done, name="join_done"),
]
