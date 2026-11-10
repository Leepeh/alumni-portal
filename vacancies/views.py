from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from core.breadcrumbs import crumbs

from .forms import ResponseForm
from .models import Partner, Vacancy


def vacancy_list(request):
    """Список вакансий и стажировок с фильтром по типу."""
    kind = request.GET.get("kind", "")
    vacancies = Vacancy.objects.select_related("partner")
    if kind == "internship":
        vacancies = vacancies.filter(is_internship=True)
    elif kind == "job":
        vacancies = vacancies.filter(is_internship=False)
    page = Paginator(vacancies, 8).get_page(request.GET.get("page"))
    return render(request, "vacancies/list.html", {
        "page": page,
        "kind": kind,
        "crumbs": crumbs("Вакансии"),
    })


def vacancy_detail(request, pk):
    """Карточка вакансии и форма отклика для выпускника."""
    vacancy = get_object_or_404(Vacancy.objects.select_related("partner"), pk=pk)
    user = request.user
    profile = getattr(user, "alumni_profile", None) if user.is_authenticated else None
    already_responded = bool(profile) and vacancy.responses.filter(profile=profile).exists()
    can_respond = bool(profile) and user.is_alumnus and vacancy.is_open and not already_responded

    form = ResponseForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if not can_respond:
            messages.error(request, "Отклик на эту вакансию недоступен.")
            return redirect("vacancies:detail", pk=pk)
        if form.is_valid():
            response = form.save(commit=False)
            response.vacancy = vacancy
            response.profile = profile
            response.save()
            messages.success(request, "Отклик отправлен. Резюме передано в Центр карьеры.")
            return redirect("vacancies:detail", pk=pk)

    return render(request, "vacancies/detail.html", {
        "vacancy": vacancy,
        "form": form,
        "can_respond": can_respond,
        "already_responded": already_responded,
        "crumbs": crumbs(("Вакансии", "vacancies:list"), vacancy.title),
    })


def partner_list(request):
    """Партнёры клуба с числом открытых вакансий."""
    partners = Partner.objects.prefetch_related("vacancies")
    return render(request, "vacancies/partners.html", {
        "partners": partners,
        "crumbs": crumbs("Партнёры"),
    })
