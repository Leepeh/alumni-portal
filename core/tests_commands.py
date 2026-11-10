import shutil
import tempfile
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role, User
from club.models import AlumniProfile, GraduateRecord
from events.models import Event
from news.models import News
from vacancies.models import Vacancy

TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class SeedDemoTests(TestCase):
    """Команда заполнения демонстрационными данными."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def test_seed_creates_three_roles_and_content(self):
        call_command("seed_demo", stdout=StringIO())
        for code in (Role.ADMIN, Role.MODERATOR, Role.ALUMNUS):
            self.assertTrue(User.objects.filter(role__code=code).exists())
        self.assertGreaterEqual(AlumniProfile.objects.count(), 10)
        self.assertTrue(GraduateRecord.objects.exists())
        self.assertTrue(Event.objects.exists())
        self.assertTrue(News.published.exists())
        self.assertTrue(Vacancy.objects.exists())

    def test_demo_accounts_can_log_in(self):
        call_command("seed_demo", stdout=StringIO())
        from core.management.commands.seed_demo import DEMO_ACCOUNTS
        for email, password, _ in DEMO_ACCOUNTS:
            with self.subTest(account=email):
                self.assertTrue(self.client.login(username=email, password=password))
                self.client.logout()

    def test_seed_does_not_run_twice_without_force(self):
        call_command("seed_demo", stdout=StringIO())
        users = User.objects.count()
        output = StringIO()
        call_command("seed_demo", stdout=output)
        self.assertEqual(User.objects.count(), users)
        self.assertIn("--force", output.getvalue())

    def test_no_empty_public_pages_after_seed(self):
        call_command("seed_demo", stdout=StringIO())
        for name, marker in (("news:list", "Читать полностью"), ("events:list", "Подробнее"),
                             ("vacancies:list", "list-group-item"), ("core:gallery", "gallery-thumb"),
                             ("vacancies:partners", "Предложений на портале")):
            with self.subTest(page=name):
                self.assertContains(self.client.get(reverse(name)), marker)


class HealthCheckTests(TestCase):
    """Проверка работоспособности для хостинга."""

    def test_health_endpoint(self):
        response = self.client.get(reverse("core:health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
