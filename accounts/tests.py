from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .decorators import role_required
from .models import Role, User


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
