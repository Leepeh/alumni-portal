from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class Role(models.Model):
    """Справочник ролей пользователей портала."""

    ADMIN = "admin"
    MODERATOR = "moderator"
    ALUMNUS = "alumnus"

    code = models.CharField("Код", max_length=20, unique=True)
    name = models.CharField("Название", max_length=50)

    class Meta:
        db_table = "roles"
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    """Создание пользователей: логином служит адрес электронной почты."""

    def create_user(self, email, password=None, role_code=Role.ALUMNUS, **extra):
        if not email:
            raise ValueError("Не указан адрес электронной почты")
        role = Role.objects.get(code=role_code)
        user = self.model(email=self.normalize_email(email).lower(), role=role, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        return self.create_user(email, password, role_code=Role.ADMIN, **extra)


class User(AbstractBaseUser):
    """Учётная запись пользователя портала."""

    email = models.EmailField("Электронная почта", max_length=254, unique=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, verbose_name="Роль",
                             related_name="users")
    is_active = models.BooleanField("Активна", default=True)
    created_at = models.DateTimeField("Дата регистрации", auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["email"]

    def __str__(self):
        return self.email

    @property
    def is_admin(self):
        return self.role.code == Role.ADMIN

    @property
    def is_moderator(self):
        # Администратору доступны и все возможности модератора
        return self.role.code in (Role.MODERATOR, Role.ADMIN)

    @property
    def is_alumnus(self):
        return self.role.code == Role.ALUMNUS


class Notification(models.Model):
    """Уведомление пользователя в личном кабинете."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь",
                             related_name="notifications")
    text = models.CharField("Текст", max_length=300)
    url = models.CharField("Ссылка", max_length=200, blank=True)
    is_read = models.BooleanField("Прочитано", default=False)
    created_at = models.DateTimeField("Дата", auto_now_add=True)

    class Meta:
        db_table = "notifications"
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]

    def __str__(self):
        return self.text


def notify(user, text, url=""):
    """Создаёт уведомление для пользователя."""
    return Notification.objects.create(user=user, text=text, url=url)
