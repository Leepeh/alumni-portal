from django.db import models
from django.utils import timezone

from core.validators import validate_document_file, validate_image_file


class Partner(models.Model):
    """Организация-партнёр клуба (работодатель)."""

    name = models.CharField("Название", max_length=200, unique=True)
    description = models.TextField("Описание", blank=True)
    site = models.URLField("Сайт", blank=True)
    logo = models.ImageField("Логотип", upload_to="partners/", blank=True,
                             validators=[validate_image_file])

    class Meta:
        db_table = "partners"
        verbose_name = "Партнёр"
        verbose_name_plural = "Партнёры"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Vacancy(models.Model):
    """Вакансия или стажировка от партнёра."""

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, verbose_name="Партнёр",
                                related_name="vacancies")
    title = models.CharField("Название", max_length=200)
    description = models.TextField("Описание", blank=True)
    salary = models.CharField("Условия оплаты", max_length=100, blank=True)
    is_internship = models.BooleanField("Стажировка", default=False)
    closes_at = models.DateField("Дата окончания приёма откликов", null=True, blank=True)
    created_at = models.DateTimeField("Дата размещения", auto_now_add=True)

    class Meta:
        db_table = "vacancies"
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.partner})"

    @property
    def is_open(self):
        """Отклики принимаются до даты окончания включительно."""
        return self.closes_at is None or self.closes_at >= timezone.localdate()


class VacancyResponse(models.Model):
    """Отклик выпускника на вакансию с приложенным резюме."""

    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, verbose_name="Вакансия",
                                related_name="responses")
    profile = models.ForeignKey("club.AlumniProfile", on_delete=models.CASCADE,
                                verbose_name="Выпускник", related_name="responses")
    resume_file = models.FileField("Файл резюме", upload_to="resumes/",
                                   validators=[validate_document_file])
    cover_letter = models.TextField("Сопроводительное письмо", blank=True)
    created_at = models.DateTimeField("Дата отклика", auto_now_add=True)

    class Meta:
        db_table = "vacancy_responses"
        verbose_name = "Отклик на вакансию"
        verbose_name_plural = "Отклики на вакансии"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["vacancy", "profile"], name="uniq_vacancy_profile"),
        ]

    def __str__(self):
        return f"{self.profile} → {self.vacancy}"
