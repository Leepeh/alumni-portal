from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

# Версия текста согласия на обработку персональных данных,
# которая показывается в формах портала
CONSENT_VERSION = "1.0"


class Faculty(models.Model):
    """Справочник факультетов."""

    name = models.CharField("Название", max_length=150, unique=True)

    class Meta:
        db_table = "faculties"
        verbose_name = "Факультет"
        verbose_name_plural = "Факультеты"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Program(models.Model):
    """Справочник направлений подготовки."""

    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT, verbose_name="Факультет",
                                related_name="programs")
    code = models.CharField("Код направления", max_length=10)
    name = models.CharField("Название", max_length=150)

    class Meta:
        db_table = "programs"
        verbose_name = "Направление подготовки"
        verbose_name_plural = "Направления подготовки"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(fields=["code", "name"], name="uniq_program_code_name"),
        ]

    def __str__(self):
        return f"{self.code} {self.name}"


class AlumniProfile(models.Model):
    """Профиль выпускника — члена клуба."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                verbose_name="Пользователь", related_name="alumni_profile")
    program = models.ForeignKey(Program, on_delete=models.PROTECT, null=True, blank=True,
                                verbose_name="Направление подготовки", related_name="alumni")
    last_name = models.CharField("Фамилия", max_length=100)
    first_name = models.CharField("Имя", max_length=100)
    middle_name = models.CharField("Отчество", max_length=100, blank=True)
    grad_year = models.PositiveSmallIntegerField(
        "Год выпуска", validators=[MinValueValidator(1990), MaxValueValidator(2100)])
    workplace = models.CharField("Место работы", max_length=255, blank=True)
    position = models.CharField("Должность", max_length=150, blank=True)
    photo = models.ImageField("Фотография", upload_to="photos/", blank=True)
    is_mentor = models.BooleanField("Готов быть наставником", default=False)

    class Meta:
        db_table = "alumni_profiles"
        verbose_name = "Профиль выпускника"
        verbose_name_plural = "Профили выпускников"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return " ".join(p for p in (self.last_name, self.first_name, self.middle_name) if p)


class RequestStatus(models.Model):
    """Справочник статусов заявок на вступление."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

    code = models.CharField("Код", max_length=20, unique=True)
    name = models.CharField("Название", max_length=50)

    class Meta:
        db_table = "request_statuses"
        verbose_name = "Статус заявки"
        verbose_name_plural = "Статусы заявок"

    def __str__(self):
        return self.name


class MembershipRequest(models.Model):
    """Заявка на вступление в клуб, которую подаёт гость портала."""

    last_name = models.CharField("Фамилия", max_length=100)
    first_name = models.CharField("Имя", max_length=100)
    middle_name = models.CharField("Отчество", max_length=100, blank=True)
    email = models.EmailField("Электронная почта", max_length=254)
    program = models.ForeignKey(Program, on_delete=models.PROTECT,
                                verbose_name="Направление подготовки", related_name="requests")
    grad_year = models.PositiveSmallIntegerField(
        "Год выпуска", validators=[MinValueValidator(1990), MaxValueValidator(2100)])
    status = models.ForeignKey(RequestStatus, on_delete=models.PROTECT, verbose_name="Статус",
                               related_name="requests")
    consent_version = models.CharField("Версия согласия на обработку ПДн", max_length=20)
    submitted_at = models.DateTimeField("Дата подачи", default=timezone.now)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, verbose_name="Кем рассмотрена",
                                    related_name="reviewed_requests")
    reviewed_at = models.DateTimeField("Дата рассмотрения", null=True, blank=True)
    comment = models.CharField("Комментарий модератора", max_length=255, blank=True)

    class Meta:
        db_table = "membership_requests"
        verbose_name = "Заявка на вступление"
        verbose_name_plural = "Заявки на вступление"
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.email})"


class PdConsent(models.Model):
    """Согласие пользователя на обработку персональных данных."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             verbose_name="Пользователь", related_name="consents")
    version = models.CharField("Версия текста согласия", max_length=20)
    given_at = models.DateTimeField("Дата предоставления")
    revoked_at = models.DateTimeField("Дата отзыва", null=True, blank=True)

    class Meta:
        db_table = "pd_consents"
        verbose_name = "Согласие на обработку ПДн"
        verbose_name_plural = "Согласия на обработку ПДн"
        ordering = ["-given_at"]

    def __str__(self):
        return f"{self.user} — версия {self.version}"

    @property
    def is_active(self):
        return self.revoked_at is None
