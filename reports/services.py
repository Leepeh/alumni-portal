"""Формирование статистики и документов: списки в .xlsx, отчёт о деятельности в .docx."""
from django.db.models import Count, Q
from django.utils import timezone
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from club.models import AlumniProfile, Faculty, MembershipRequest, RequestStatus
from events.models import Event, EventRegistration
from feedback.models import Feedback
from news.models import News
from vacancies.models import Vacancy, VacancyResponse

XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


# --- статистика ------------------------------------------------------------

def members_by_faculty():
    """Число членов клуба по факультетам."""
    return (Faculty.objects.annotate(total=Count("programs__alumni"))
            .values_list("name", "total").order_by("-total", "name"))


def members_by_year():
    """Число членов клуба по годам выпуска."""
    return (AlumniProfile.objects.values_list("grad_year")
            .annotate(total=Count("id")).order_by("grad_year"))


def requests_by_status():
    """Число заявок на вступление по статусам."""
    return (RequestStatus.objects.annotate(total=Count("requests"))
            .values_list("name", "total").order_by("id"))


def period_indicators(date_from, date_to):
    """Показатели деятельности клуба за период (обе даты включительно)."""
    in_period = {"__date__gte": date_from, "__date__lte": date_to}

    def between(field):
        return {field + key: value for key, value in in_period.items()}

    requests = MembershipRequest.objects.filter(**between("submitted_at"))
    registrations = EventRegistration.objects.filter(**between("event__start_at"))
    feedback = Feedback.objects.filter(**between("created_at"))
    return [
        ("Подано заявок на вступление", requests.count()),
        ("Одобрено заявок", requests.filter(status__code=RequestStatus.APPROVED).count()),
        ("Отклонено заявок", requests.filter(status__code=RequestStatus.REJECTED).count()),
        ("Проведено мероприятий", Event.objects.filter(**between("start_at")).count()),
        ("Регистраций на мероприятия", registrations.count()),
        ("Отмечено посещений", registrations.filter(attended=True).count()),
        ("Опубликовано новостей и историй", News.objects.filter(**between("published_at")).count()),
        ("Размещено вакансий и стажировок", Vacancy.objects.filter(**between("created_at")).count()),
        ("Получено откликов на вакансии",
         VacancyResponse.objects.filter(**between("created_at")).count()),
        ("Получено обращений", feedback.count()),
        ("Обработано обращений", feedback.filter(is_processed=True).count()),
    ]


def events_in_period(date_from, date_to):
    """Мероприятия за период с числом регистраций и посещений."""
    return (Event.objects.filter(start_at__date__gte=date_from, start_at__date__lte=date_to)
            .annotate(registered=Count("registrations"),
                      attended=Count("registrations", filter=Q(registrations__attended=True)))
            .order_by("start_at"))


# --- книги Excel -----------------------------------------------------------

def _fill_sheet(sheet, header, rows):
    """Записывает заголовок и строки, выделяет заголовок и подбирает ширину столбцов."""
    sheet.append(header)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in rows:
        sheet.append(row)
    for index, title in enumerate(header, start=1):
        longest = max([len(str(title))] + [len(str(row[index - 1] or "")) for row in rows])
        sheet.column_dimensions[get_column_letter(index)].width = min(longest + 2, 50)
    sheet.freeze_panes = "A2"


def participants_workbook(event):
    """Список участников мероприятия для выгрузки в .xlsx."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Участники"
    rows = []
    registrations = event.registrations.select_related("profile__program", "profile__user")
    for number, registration in enumerate(registrations, start=1):
        profile = registration.profile
        rows.append([
            number, profile.last_name, profile.first_name, profile.middle_name,
            # У выпускника может быть не указано направление подготовки
            profile.program.name if profile.program else "",
            profile.grad_year, profile.user.email,
            "Да" if registration.attended else "Нет",
        ])
    _fill_sheet(sheet, ["№", "Фамилия", "Имя", "Отчество", "Направление", "Год выпуска",
                        "E-mail", "Посещение"], rows)
    return workbook


def members_workbook():
    """Реестр членов клуба для выгрузки в .xlsx."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Члены клуба"
    rows = []
    profiles = AlumniProfile.objects.filter(user__is_active=True).select_related(
        "program__faculty", "user")
    for number, profile in enumerate(profiles, start=1):
        rows.append([
            number, profile.last_name, profile.first_name, profile.middle_name,
            profile.program.faculty.name if profile.program else "",
            profile.program.name if profile.program else "",
            profile.grad_year, profile.workplace, profile.position, profile.user.email,
            "Да" if profile.is_mentor else "Нет",
        ])
    _fill_sheet(sheet, ["№", "Фамилия", "Имя", "Отчество", "Факультет", "Направление",
                        "Год выпуска", "Место работы", "Должность", "E-mail", "Наставник"], rows)
    return workbook


# --- отчёт Word ------------------------------------------------------------

def _add_table(document, header, rows):
    table = document.add_table(rows=1, cols=len(header))
    table.style = "Table Grid"
    for cell, title in zip(table.rows[0].cells, header):
        cell.text = str(title)
        cell.paragraphs[0].runs[0].font.bold = True
    for row in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = str(value)
    return table


def activity_report(date_from, date_to, author):
    """Отчёт о деятельности клуба выпускников за период в формате .docx."""
    document = Document()
    style = document.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)

    title = document.add_heading("Отчёт о деятельности клуба выпускников", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    period = document.add_paragraph(
        f"за период с {date_from:%d.%m.%Y} по {date_to:%d.%m.%Y}")
    period.alignment = WD_ALIGN_PARAGRAPH.CENTER

    document.add_heading("1. Основные показатели", level=2)
    _add_table(document, ["Показатель", "Значение"], period_indicators(date_from, date_to))

    document.add_heading("2. Мероприятия за период", level=2)
    events = [(event.start_at.strftime("%d.%m.%Y"), event.title, event.capacity,
               event.registered, event.attended)
              for event in events_in_period(date_from, date_to)]
    if events:
        _add_table(document, ["Дата", "Мероприятие", "Мест", "Регистраций", "Посещений"], events)
    else:
        document.add_paragraph("В указанный период мероприятия не проводились.")

    document.add_heading("3. Состав клуба по факультетам", level=2)
    total = AlumniProfile.objects.count()
    _add_table(document, ["Факультет", "Членов клуба"],
               list(members_by_faculty()) + [("Итого", total)])

    document.add_paragraph()
    document.add_paragraph(
        f"Отчёт сформирован {timezone.localtime():%d.%m.%Y %H:%M} на портале клуба "
        f"выпускников. Составитель: {author}.")
    return document
