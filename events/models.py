from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class EventStatus(models.Model):
    """Справочник статусов мероприятий."""

    PLANNED = "planned"
    OPEN = "open"
    FINISHED = "finished"
    CANCELLED = "cancelled"

    code = models.CharField("Код", max_length=20, unique=True)
    name = models.CharField("Название", max_length=50)

    class Meta:
        db_table = "event_statuses"
        verbose_name = "Статус мероприятия"
        verbose_name_plural = "Статусы мероприятий"

    def __str__(self):
        return self.name


class Event(models.Model):
    """Мероприятие клуба выпускников."""

    title = models.CharField("Название", max_length=200)
    description = models.TextField("Описание", blank=True)
    start_at = models.DateTimeField("Дата и время начала")
    place = models.CharField("Место проведения", max_length=255, blank=True)
    capacity = models.PositiveIntegerField("Количество мест",
                                           validators=[MinValueValidator(1)])
    status = models.ForeignKey(EventStatus, on_delete=models.PROTECT, verbose_name="Статус",
                               related_name="events")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, verbose_name="Автор", related_name="events")

    class Meta:
        db_table = "events"
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"
        ordering = ["start_at"]
        indexes = [models.Index(fields=["start_at"], name="idx_events_date")]

    def __str__(self):
        return self.title

    def free_places(self):
        # Свободные места = вместимость минус число регистраций
        return max(self.capacity - self.registrations.count(), 0)

    @property
    def is_registration_open(self):
        """Запись возможна, пока статус «Регистрация открыта» и событие не началось."""
        return self.status.code == EventStatus.OPEN and self.start_at > timezone.now()


class EventRegistration(models.Model):
    """Регистрация выпускника на мероприятие."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Мероприятие",
                              related_name="registrations")
    profile = models.ForeignKey("club.AlumniProfile", on_delete=models.CASCADE,
                                verbose_name="Выпускник", related_name="registrations")
    registered_at = models.DateTimeField("Дата регистрации", auto_now_add=True)
    attended = models.BooleanField("Отметка о посещении", default=False)

    class Meta:
        db_table = "event_registrations"
        verbose_name = "Регистрация на мероприятие"
        verbose_name_plural = "Регистрации на мероприятия"
        ordering = ["registered_at"]
        constraints = [
            models.UniqueConstraint(fields=["event", "profile"], name="uniq_event_profile"),
        ]

    def __str__(self):
        return f"{self.profile} → {self.event}"
