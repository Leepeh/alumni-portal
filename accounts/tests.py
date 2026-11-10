import io
import shutil
import tempfile

from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from club.models import PdConsent
from core.testutils import PASSWORD, make_alumnus, make_moderator
from vacancies.models import Partner, Vacancy, VacancyResponse

from .decorators import role_required
from .models import Role, User, notify

TEMP_MEDIA = tempfile.mkdtemp()


class UserModelTests(TestCase):
    """Проверка модели пользователя и ролей."""

    def test_roles_created_by_migration(self):
        codes = set(Role.objects.values_list("code", flat=True))
        self.assertEqual(codes, {Role.ADMIN, Role.MODERATOR, Role.ALUMNUS})

    def test_default_role_is_alumnus(self):
        user = User.objects.create_user("New@Example.ru", "pass-12345")
        self.assertEqual(user.email, "new@example.ru")
        self.assertTrue(user.is_alumnus)
        self.assertFalse(user.is_moderator)

    def test_admin_has_moderator_rights(self):
        admin = User.objects.create_superuser("admin@example.ru", "pass-12345")
        self.assertTrue(admin.is_admin)
        self.assertTrue(admin.is_moderator)

    def test_password_is_stored_as_hash(self):
        user = User.objects.create_user("hash@example.ru", "pass-12345")
        self.assertNotEqual(user.password, "pass-12345")
        self.assertTrue(user.check_password("pass-12345"))


class AccessTests(TestCase):
    """Проверка входа и разграничения доступа по ролям."""

    def setUp(self):
        self.alumnus = User.objects.create_user("alumnus@example.ru", "pass-12345")
        self.moderator = User.objects.create_user("moder@example.ru", "pass-12345",
                                                  role_code=Role.MODERATOR)

    def test_cabinet_requires_login(self):
        response = self.client.get(reverse("accounts:cabinet"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next=/accounts/cabinet/")

    def test_login_with_email_in_any_case(self):
        response = self.client.post(reverse("accounts:login"),
                                    {"username": "ALUMNUS@example.ru", "password": "pass-12345"})
        self.assertRedirects(response, reverse("core:home"))

    def test_login_with_wrong_password(self):
        response = self.client.post(reverse("accounts:login"),
                                    {"username": "alumnus@example.ru", "password": "wrong"})
        self.assertContains(response, "Неверная электронная почта или пароль")

    def test_role_required_blocks_other_roles(self):
        view = role_required(Role.MODERATOR)(lambda request: HttpResponse("ok"))
        request = RequestFactory().get("/")
        request.user = self.alumnus
        with self.assertRaises(PermissionDenied):
            view(request)
        request.user = self.moderator
        self.assertEqual(view(request).status_code, 200)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class CabinetTests(TestCase):
    """Личный кабинет выпускника."""

    pages = ["accounts:cabinet", "accounts:profile", "accounts:my_events",
             "accounts:my_responses", "accounts:notifications", "accounts:consents",
             "accounts:password"]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.alumnus = make_alumnus()
        self.client.login(username=self.alumnus.email, password=PASSWORD)

    def test_at_least_five_cabinet_pages(self):
        self.assertGreaterEqual(len(self.pages), 5)
        for name in self.pages:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'class="breadcrumb"')

    def test_cabinet_pages_closed_for_guest(self):
        self.client.logout()
        for name in self.pages:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 302)

    def test_staff_is_redirected_to_own_cabinet(self):
        self.client.logout()
        moderator = make_moderator()
        self.client.login(username=moderator.email, password=PASSWORD)
        self.assertRedirects(self.client.get(reverse("accounts:cabinet")),
                             reverse("moderation:home"))
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 403)

    def test_profile_is_saved_and_photo_is_resized(self):
        buffer = io.BytesIO()
        Image.new("RGB", (2000, 1500), (20, 60, 110)).save(buffer, format="JPEG")
        photo = SimpleUploadedFile("photo.jpg", buffer.getvalue(), content_type="image/jpeg")
        profile = self.alumnus.alumni_profile
        self.client.post(reverse("accounts:profile"), {
            "last_name": "Тестов", "first_name": "Иван", "grad_year": 2020,
            "program": profile.program.pk, "workplace": "ООО «Пример»", "photo": photo})
        profile.refresh_from_db()
        self.assertEqual(profile.workplace, "ООО «Пример»")
        with Image.open(profile.photo.path) as saved:
            self.assertLessEqual(max(saved.size), 600)

    def test_wrong_photo_type_is_rejected(self):
        profile = self.alumnus.alumni_profile
        response = self.client.post(reverse("accounts:profile"), {
            "last_name": "Тестов", "first_name": "Иван", "grad_year": 2020,
            "program": profile.program.pk,
            "photo": SimpleUploadedFile("photo.txt", b"not an image")})
        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertFalse(profile.photo)

    def test_notifications_are_marked_read_after_opening(self):
        notify(self.alumnus, "Вы зарегистрированы на мероприятие")
        self.client.get(reverse("accounts:notifications"))
        self.assertEqual(self.alumnus.notifications.filter(is_read=False).count(), 0)

    def test_consent_revoke_disables_account(self):
        PdConsent.objects.create(user=self.alumnus, version="1.0", given_at=timezone.now())
        self.client.post(reverse("accounts:consent_revoke"))
        self.alumnus.refresh_from_db()
        self.assertFalse(self.alumnus.is_active)
        self.assertFalse(self.alumnus.consents.filter(revoked_at__isnull=True).exists())
        self.assertFalse(self.client.login(username=self.alumnus.email, password=PASSWORD))

    def test_password_change(self):
        self.client.post(reverse("accounts:password"), {
            "old_password": PASSWORD, "new_password1": "New-pass-2026",
            "new_password2": "New-pass-2026"})
        self.alumnus.refresh_from_db()
        self.assertTrue(self.alumnus.check_password("New-pass-2026"))


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class MediaAccessTests(TestCase):
    """Резюме из откликов доступны только автору и сотрудникам."""

    def setUp(self):
        self.owner = make_alumnus()
        partner = Partner.objects.create(name="ООО «Тест»")
        vacancy = Vacancy.objects.create(partner=partner, title="Аналитик")
        self.response = VacancyResponse.objects.create(
            vacancy=vacancy, profile=self.owner.alumni_profile,
            resume_file=SimpleUploadedFile("cv.pdf", b"resume"))
        self.url = self.response.resume_file.url

    def test_guest_and_other_alumnus_cannot_download(self):
        self.assertEqual(self.client.get(self.url).status_code, 403)
        other = make_alumnus("other@example.ru")
        self.client.login(username=other.email, password=PASSWORD)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_owner_and_moderator_can_download(self):
        for user in (self.owner, make_moderator()):
            self.client.login(username=user.email, password=PASSWORD)
            self.assertEqual(self.client.get(self.url).status_code, 200)
            self.client.logout()
