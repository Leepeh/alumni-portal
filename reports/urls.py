from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("events/<int:pk>/participants.xlsx", views.participants_xlsx, name="participants_xlsx"),
    path("members.xlsx", views.members_xlsx, name="members_xlsx"),
]
