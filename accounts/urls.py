from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("cabinet/", views.cabinet, name="cabinet"),
    path("cabinet/profile/", views.profile_edit, name="profile"),
    path("cabinet/events/", views.my_events, name="my_events"),
    path("cabinet/responses/", views.my_responses, name="my_responses"),
    path("cabinet/notifications/", views.notifications, name="notifications"),
    path("cabinet/consents/", views.consents, name="consents"),
    path("cabinet/consents/revoke/", views.consent_revoke, name="consent_revoke"),
    path("cabinet/password/", views.PasswordChangeView.as_view(), name="password"),
]
