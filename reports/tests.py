import io
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from docx import Document
from openpyxl import load_workbook

from core.testutils import PASSWORD, make_admin, make_alumnus, make_moderator
from events.models import Event, EventRegistration, EventStatus

from . import services


class ExportTests(TestCase):
    """Формирование документов .xlsx и .docx."""

    def setUp(self):
        self.event = Event.objects.create(
            title="День карьеры", capacity=10, start_at=timezone.now() - timedelta(days=2),
            status=EventStatus.objects.get(code=EventStatus.FINISHED))
        self.first = make_alumnus("first@example.ru", "Белов", "Никита")
        self.second = make_alumnus("second@example.ru", "Орлова", "Анна")
        EventRegistration.objects.create(event=self.event, profile=self.first.alumni_profile,
                                         attended=True)
        EventRegistration.objects.create(event=self.event, profile=self.second.alumni_profile)

    def login(self, user):
        self.client.login(username=user.email, password=PASSWORD)

    def test_participants_xlsx_matches_database(self):
        self.login(make_moderator())
        response = self.client.get(reverse("reports:participants_xlsx", args=[self.event.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], services.XLSX_TYPE)
        sheet = load_workbook(io.BytesIO(response.content)).active
        rows = list(sheet.iter_rows(values_only=True))
        self.assertEqual(rows[0][1], "Фамилия")
        self.assertEqual(len(rows) - 1, self.event.registrations.count())
        self.assertEqual({row[6] for row in rows[1:]}, {"first@example.ru", "second@example.ru"})

    def test_xlsx_export_works_without_program(self):
        profile = self.first.alumni_profile
        profile.program = None
        profile.save()
        self.login(make_moderator())
        response = self.client.get(reverse("reports:participants_xlsx", args=[self.event.pk]))
        self.assertEqual(response.status_code, 200)

    def test_alumnus_cannot_export_participants(self):
        self.login(self.first)
        response = self.client.get(reverse("reports:participants_xlsx", args=[self.event.pk]))
        self.assertEqual(response.status_code, 403)

    def test_members_xlsx_only_for_admin(self):
        self.login(make_moderator())
        self.assertEqual(self.client.get(reverse("reports:members_xlsx")).status_code, 403)
        self.client.logout()
        self.login(make_admin())
        response = self.client.get(reverse("reports:members_xlsx"))
        sheet = load_workbook(io.BytesIO(response.content)).active
        self.assertEqual(sheet.max_row - 1, 2)

    def test_activity_report_docx(self):
        self.login(make_admin())
        today = timezone.localdate()
        response = self.client.post(reverse("panel:reports"), {
            "date_from": (today - timedelta(days=30)).isoformat(), "date_to": today.isoformat()})
        self.assertEqual(response["Content-Type"], services.DOCX_TYPE)
        document = Document(io.BytesIO(response.content))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        self.assertIn("Отчёт о деятельности клуба выпускников", text)
        indicators = {row.cells[0].text: row.cells[1].text for row in document.tables[0].rows}
        self.assertEqual(indicators["Проведено мероприятий"], "1")
        self.assertEqual(indicators["Отмечено посещений"], "1")

    def test_report_period_is_validated(self):
        self.login(make_admin())
        response = self.client.post(reverse("panel:reports"), {
            "date_from": "2026-12-01", "date_to": "2026-01-01"})
        self.assertContains(response, "не может быть позже")
