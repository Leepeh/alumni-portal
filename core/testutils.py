"""Вспомогательные функции для автотестов: создание тестовых пользователей."""
from accounts.models import Role, User
from club.models import AlumniProfile, Program

PASSWORD = "pass-12345"


def make_alumnus(email="alumnus@example.ru", last_name="Тестов", first_name="Иван"):
    """Создаёт выпускника с профилем члена клуба."""
    user = User.objects.create_user(email, PASSWORD)
    AlumniProfile.objects.create(user=user, program=Program.objects.first(),
                                 last_name=last_name, first_name=first_name, grad_year=2020)
    return user


def make_moderator(email="moder@example.ru"):
    return User.objects.create_user(email, PASSWORD, role_code=Role.MODERATOR)


def make_admin(email="admin@example.ru"):
    return User.objects.create_user(email, PASSWORD, role_code=Role.ADMIN)
