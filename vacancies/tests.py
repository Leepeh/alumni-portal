import shutil
import tempfile
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.testutils import PASSWORD, make_alumnus

from .models import Partner, Vacancy

TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class VacancyResponseTests(TestCase):
    """Проверка отклика на вакансию и загрузки резюме."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.alumnus = make_alumnus()
        partner = Partner.objects.create(name="ООО «Тестовая компания»")
        self.vacancy = Vacancy.objects.create(partner=partner, title="Бизнес-аналитик")
        self.url = reverse("vacancies:detail", args=[self.vacancy.pk])
        self.client.login(username=self.alumnus.email, password=PASSWORD)

    def resume(self, name="resume.pdf", size=1024):
        return SimpleUploadedFile(name, b"x" * size, content_type="application/pdf")

    def test_response_with_resume_is_saved(self):
        self.client.post(self.url, {"resume_file": self.resume(), "cover_letter": "Добрый день"})
        self.assertEqual(self.vacancy.responses.count(), 1)

    def test_wrong_file_type_is_rejected(self):
        response = self.client.post(self.url, {"resume_file": self.resume("virus.exe")})
        self.assertContains(response, "Недопустимый тип файла")
        self.assertEqual(self.vacancy.responses.count(), 0)

    def test_too_large_file_is_rejected(self):
        response = self.client.post(self.url, {"resume_file": self.resume(size=6 * 1024 * 1024)})
        self.assertContains(response, "не должен превышать")
        self.assertEqual(self.vacancy.responses.count(), 0)

    def test_second_response_is_not_accepted(self):
        self.client.post(self.url, {"resume_file": self.resume()})
        self.client.post(self.url, {"resume_file": self.resume("second.pdf")})
        self.assertEqual(self.vacancy.responses.count(), 1)

    def test_closed_vacancy_does_not_accept_responses(self):
        self.vacancy.closes_at = timezone.localdate() - timedelta(days=1)
        self.vacancy.save()
        self.client.post(self.url, {"resume_file": self.resume()})
        self.assertEqual(self.vacancy.responses.count(), 0)

    def test_guest_cannot_respond(self):
        self.client.logout()
        self.client.post(self.url, {"resume_file": self.resume()})
        self.assertEqual(self.vacancy.responses.count(), 0)
