from django.urls import path

from accounts.models import Role
from core.crud import Crud
from core.models import ClubDocument, GalleryPhoto
from events.models import Event
from news.models import News
from vacancies.models import Partner, Vacancy

from . import forms, views

app_name = "moderation"

COMMON = {
    "namespace": app_name,
    "roles": (Role.MODERATOR, Role.ADMIN),
    "base_template": "layouts/cabinet.html",
    "section_crumb": ("Кабинет модератора", "moderation:home"),
}

# Разделы управления содержимым портала
SECTIONS = [
    Crud(model=News, form_class=forms.NewsForm, name="news", title="Новости и истории",
         title_one="публикацию", user_field="author",
         columns=[("Заголовок", "title"), ("Категория", "category.name"),
                  ("Опубликовано", "published_at")], **COMMON),
    Crud(model=Event, form_class=forms.EventForm, name="events", title="Мероприятия",
         title_one="мероприятие", user_field="created_by",
         columns=[("Название", "title"), ("Начало", "start_at"), ("Статус", "status.name"),
                  ("Свободно мест", "free_places")],
         extra_actions=[("Участники", "moderation:participants")], **COMMON),
    Crud(model=Partner, form_class=forms.PartnerForm, name="partners", title="Партнёры",
         title_one="партнёра", columns=[("Название", "name"), ("Сайт", "site")], **COMMON),
    Crud(model=Vacancy, form_class=forms.VacancyForm, name="vacancies", title="Вакансии",
         title_one="вакансию",
         columns=[("Название", "title"), ("Партнёр", "partner.name"),
                  ("Стажировка", "is_internship"), ("Отклики до", "closes_at")], **COMMON),
    Crud(model=GalleryPhoto, form_class=forms.GalleryForm, name="gallery", title="Галерея",
         title_one="фотографию", user_field="uploaded_by",
         columns=[("Подпись", "title"), ("Дата съёмки", "taken_at"),
                  ("Загружено", "uploaded_at")], **COMMON),
    Crud(model=ClubDocument, form_class=forms.DocumentForm, name="documents",
         title="Документы клуба", title_one="документ", user_field="uploaded_by",
         columns=[("Название", "title"), ("Размещён", "uploaded_at")], **COMMON),
]

urlpatterns = [
    path("", views.home, name="home"),
    path("requests/", views.request_list, name="requests"),
    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("feedback/", views.feedback_list, name="feedback"),
    path("feedback/<int:pk>/", views.feedback_detail, name="feedback_detail"),
    path("responses/", views.response_list, name="responses"),
    path("events/<int:pk>/participants/", views.participants, name="participants"),
    path("attendance/<int:pk>/", views.toggle_attendance, name="toggle_attendance"),
]

for section in SECTIONS:
    urlpatterns += section.urls()
