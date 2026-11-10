from django.conf import settings
from django.db import models


class Feedback(models.Model):
    """Обращение, отправленное через форму обратной связи."""

    name = models.CharField("Имя", max_length=100)
    email = models.EmailField("Электронная почта", max_length=254)
    topic = models.CharField("Тема", max_length=200, blank=True)
    message = models.TextField("Сообщение")
    consent = models.BooleanField("Согласие на обработку ПДн")
    created_at = models.DateTimeField("Дата", auto_now_add=True)
    is_processed = models.BooleanField("Обработано", default=False)
    answer = models.TextField("Ответ модератора", blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, verbose_name="Кем обработано",
                                     related_name="processed_feedback")

    class Meta:
        db_table = "feedback"
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"
        ordering = ["-created_at"]
        constraints = [
            # Обращение без согласия на обработку ПДн сохранить нельзя
            models.CheckConstraint(condition=models.Q(consent=True), name="feedback_consent_true"),
        ]

    def __str__(self):
        return f"{self.name}: {self.topic or 'без темы'}"
