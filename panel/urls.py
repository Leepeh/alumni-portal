from django.urls import path

from accounts.models import Role
from club.models import Faculty, Program
from core.crud import Crud

from . import forms, views

app_name = "panel"

COMMON = {
    "namespace": app_name,
    "roles": (Role.ADMIN,),
    "base_template": "layouts/cabinet.html",
    "section_crumb": ("Панель администратора", "panel:dashboard"),
}

# Справочники, которые ведёт администратор
SECTIONS = [
    Crud(model=Faculty, form_class=forms.FacultyForm, name="faculties", title="Факультеты",
         title_one="факультет", columns=[("Название", "name")], **COMMON),
    Crud(model=Program, form_class=forms.ProgramForm, name="programs",
         title="Направления подготовки", title_one="направление",
         columns=[("Код", "code"), ("Название", "name"), ("Факультет", "faculty.name")],
         **COMMON),
]

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/", views.user_list, name="users"),
    path("users/<int:pk>/", views.user_edit, name="user_edit"),
    path("import/", views.import_graduates, name="import"),
    path("import/template.xlsx", views.import_template, name="import_template"),
    path("reports/", views.reports, name="reports"),
    path("log/", views.action_log, name="log"),
]

for section in SECTIONS:
    urlpatterns += section.urls()
