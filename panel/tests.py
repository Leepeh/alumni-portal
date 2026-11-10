import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook

from accounts.models import Role, User
from club import importer
from club.models import Faculty, GraduateRecord
from core.models import ActionLog
from core.testutils import PASSWORD, make_admin, make_alumnus, make_moderator


def xlsx(rows, header=None):
    """Собирает в памяти файл .xlsx для импорта."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(header or importer.COLUMNS)
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return SimpleUploadedFile("graduates.xlsx", buffer.getvalue())


class AdminTestCase(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.client.login(username=self.admin.email, password=PASSWORD)


class AccessTests(AdminTestCase):
    """Панель администратора доступна только администратору."""

    pages = ["panel:dashboard", "panel:users", "panel:faculties_list", "panel:programs_list",
             "panel:import", "panel:reports", "panel:log"]

    def test_at_least_five_pages_open_for_admin(self):
        self.assertGreaterEqual(len(self.pages), 5)
        for name in self.pages:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'class="breadcrumb"')

    def test_moderator_and_alumnus_get_403(self):
        for user in (make_moderator(), make_alumnus()):
            self.client.logout()
            self.client.login(username=user.email, password=PASSWORD)
            for name in self.pages:
                with self.subTest(page=name, role=user.role.code):
                    self.assertEqual(self.client.get(reverse(name)).status_code, 403)


class UserManagementTests(AdminTestCase):
    """Управление пользователями и справочниками."""

    def test_admin_creates_moderator(self):
        role = Role.objects.get(code=Role.MODERATOR)
        response = self.client.post(reverse("panel:users"),
                                    {"email": "New.Moder@example.ru", "role": role.pk}, follow=True)
        self.assertContains(response, "временный пароль")
        self.assertTrue(User.objects.get(email="new.moder@example.ru").is_moderator)

    def test_admin_changes_role_and_blocks_user(self):
        alumnus = make_alumnus()
        self.client.post(reverse("panel:user_edit", args=[alumnus.pk]),
                         {"role": Role.objects.get(code=Role.MODERATOR).pk})
        alumnus.refresh_from_db()
        self.assertTrue(alumnus.is_moderator)
        self.assertFalse(alumnus.is_active)
        self.assertTrue(ActionLog.objects.filter(user=self.admin).exists())

    def test_admin_cannot_disable_own_account(self):
        response = self.client.post(reverse("panel:user_edit", args=[self.admin.pk]),
                                    {"role": Role.objects.get(code=Role.ADMIN).pk})
        self.assertContains(response, "Нельзя отключить собственную учётную запись")
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_faculty_in_use_cannot_be_deleted(self):
        faculty = Faculty.objects.filter(programs__isnull=False).first()
        response = self.client.post(reverse("panel:faculties_delete", args=[faculty.pk]),
                                    follow=True)
        self.assertContains(response, "удалить её нельзя")
        self.assertTrue(Faculty.objects.filter(pk=faculty.pk).exists())


class ImportTests(AdminTestCase):
    """Импорт реестра выпускников из .xlsx."""

    def post(self, file):
        return self.client.post(reverse("panel:import"), {"file": file})

    def test_valid_file_is_imported(self):
        response = self.post(xlsx([["Иванова", "Мария", "Петровна", "38.03.05", 2022],
                                   ["Петров", "Олег", "", "09.03.03", 2020]]))
        self.assertContains(response, "Добавлено записей: 2")
        self.assertEqual(GraduateRecord.objects.count(), 2)

    def test_repeated_import_updates_instead_of_duplicating(self):
        rows = [["Иванова", "Мария", "Петровна", "38.03.05", 2022]]
        self.post(xlsx(rows))
        response = self.post(xlsx(rows))
        self.assertContains(response, "обновлено: 1")
        self.assertEqual(GraduateRecord.objects.count(), 1)

    def test_file_with_errors_is_rolled_back(self):
        response = self.post(xlsx([["Иванова", "Мария", "Петровна", "38.03.05", 2022],
                                   ["Сидоров", "Иван", "", "00.00.00", 2020],
                                   ["", "Анна", "", "38.03.05", "две тысячи"]]))
        self.assertContains(response, "Импорт отменён")
        self.assertContains(response, "Строка 3")
        self.assertContains(response, "Строка 4")
        self.assertEqual(GraduateRecord.objects.count(), 0)

    def test_wrong_header_is_rejected(self):
        response = self.post(xlsx([["Иванова", "Мария"]], header=["ФИО", "Год"]))
        self.assertContains(response, "Заголовки столбцов не совпадают")

    def test_non_xlsx_file_is_rejected(self):
        response = self.post(SimpleUploadedFile("graduates.csv", b"a;b;c"))
        self.assertContains(response, "Нужен файл формата .xlsx")

    def test_template_can_be_downloaded(self):
        response = self.client.get(reverse("panel:import_template"))
        self.assertEqual(response.status_code, 200)
