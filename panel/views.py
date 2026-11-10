from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.crypto import get_random_string

from accounts.decorators import role_required
from accounts.forms import StaffCreateForm, UserEditForm
from accounts.models import Role, User
from club import importer
from club.models import AlumniProfile, GraduateRecord
from core.audit import log_action
from core.breadcrumbs import crumbs
from core.models import ActionLog
from events.models import Event
from reports import services
from vacancies.models import Vacancy

from .forms import ImportForm, ReportForm

HOME = ("Панель администратора", "panel:dashboard")


@role_required(Role.ADMIN)
def dashboard(request):
    """Статистика клуба: состав, заявки, мероприятия."""
    faculties = list(services.members_by_faculty())
    years = list(services.members_by_year())
    largest = max([total for _, total in faculties + years] or [1]) or 1
    return render(request, "panel/dashboard.html", {
        "totals": [
            ("Членов клуба", AlumniProfile.objects.count()),
            ("Пользователей", User.objects.count()),
            ("Записей в реестре выпускников", GraduateRecord.objects.count()),
            ("Мероприятий", Event.objects.count()),
            ("Вакансий", Vacancy.objects.count()),
        ],
        "faculties": [(name, total, round(total * 100 / largest)) for name, total in faculties],
        "years": [(year, total, round(total * 100 / largest)) for year, total in years],
        "requests": services.requests_by_status(),
        "crumbs": crumbs("Панель администратора"),
    })


@role_required(Role.ADMIN)
def user_list(request):
    """Список пользователей с поиском и созданием учётной записи сотрудника."""
    query = request.GET.get("q", "").strip()
    users = User.objects.select_related("role")
    if query:
        users = users.filter(Q(email__icontains=query)
                             | Q(alumni_profile__last_name__icontains=query))
    form = StaffCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        password = get_random_string(10)
        user = User.objects.create_user(form.cleaned_data["email"], password,
                                        role_code=form.cleaned_data["role"].code)
        log_action(request, "Создание учётной записи сотрудника", user)
        messages.success(request, f"Учётная запись {user.email} создана, "
                                  f"временный пароль: {password}")
        return redirect("panel:users")
    return render(request, "panel/users.html", {
        "page": Paginator(users, 20).get_page(request.GET.get("page")),
        "query": query,
        "form": form,
        "crumbs": crumbs(HOME, "Пользователи"),
    })


@role_required(Role.ADMIN)
def user_edit(request, pk):
    """Изменение роли и активности учётной записи."""
    account = get_object_or_404(User, pk=pk)
    form = UserEditForm(request.POST or None, instance=account)
    if request.method == "POST" and form.is_valid():
        if account == request.user and (not form.cleaned_data["is_active"]
                                        or form.cleaned_data["role"].code != Role.ADMIN):
            # Администратор не должен случайно лишить себя доступа к панели
            messages.error(request, "Нельзя отключить собственную учётную запись "
                                    "или снять с себя роль администратора.")
        else:
            form.save()
            log_action(request, "Изменение роли или активности пользователя", account)
            messages.success(request, "Изменения сохранены.")
            return redirect("panel:users")
    return render(request, "panel/user_edit.html", {
        "account": account,
        "form": form,
        "crumbs": crumbs(HOME, ("Пользователи", "panel:users"), account.email),
    })


@role_required(Role.ADMIN)
def import_graduates(request):
    """Импорт реестра выпускников из файла .xlsx."""
    form = ImportForm(request.POST or None, request.FILES or None)
    result = None
    if request.method == "POST" and form.is_valid():
        result = importer.import_graduates(form.cleaned_data["file"])
        if result.ok:
            log_action(request, f"Импорт реестра выпускников: добавлено {result.created}, "
                                f"обновлено {result.updated}")
    return render(request, "panel/import.html", {
        "form": form,
        "result": result,
        "columns": importer.COLUMNS,
        "registry_count": GraduateRecord.objects.count(),
        "crumbs": crumbs(HOME, "Импорт выпускников"),
    })


@role_required(Role.ADMIN)
def import_template(request):
    """Скачивание шаблона файла для импорта."""
    response = HttpResponse(content_type=services.XLSX_TYPE)
    response["Content-Disposition"] = 'attachment; filename="graduates_template.xlsx"'
    importer.template_workbook().save(response)
    return response


@role_required(Role.ADMIN)
def reports(request):
    """Формирование отчёта о деятельности клуба в .docx и выгрузка реестра в .xlsx."""
    form = ReportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        date_from, date_to = form.cleaned_data["date_from"], form.cleaned_data["date_to"]
        document = services.activity_report(date_from, date_to, request.user.email)
        response = HttpResponse(content_type=services.DOCX_TYPE)
        response["Content-Disposition"] = (
            f'attachment; filename="club_report_{date_from:%Y%m%d}_{date_to:%Y%m%d}.docx"')
        document.save(response)
        log_action(request, f"Формирование отчёта за {date_from:%d.%m.%Y}–{date_to:%d.%m.%Y}")
        return response
    return render(request, "panel/reports.html", {
        "form": form,
        "crumbs": crumbs(HOME, "Отчёты"),
    })


@role_required(Role.ADMIN)
def action_log(request):
    """Журнал действий модераторов и администраторов."""
    entries = ActionLog.objects.select_related("user")
    return render(request, "panel/log.html", {
        "page": Paginator(entries, 30).get_page(request.GET.get("page")),
        "crumbs": crumbs(HOME, "Журнал действий"),
    })
