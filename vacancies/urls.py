from django.urls import path

from . import views

app_name = "vacancies"

urlpatterns = [
    path("vacancies/", views.vacancy_list, name="list"),
    path("vacancies/<int:pk>/", views.vacancy_detail, name="detail"),
    path("partners/", views.partner_list, name="partners"),
]
