from django.conf import settings
from django.db import models
from django.utils import timezone

from core.validators import validate_image_file


class NewsCategory(models.Model):
    """Справочник категорий публикаций."""

    NEWS = "news"
    STORY = "story"

    code = models.CharField("Код", max_length=20, unique=True)
    name = models.CharField("Название", max_length=50)

    class Meta:
        db_table = "news_categories"
        verbose_name = "Категория публикации"
        verbose_name_plural = "Категории публикаций"

    def __str__(self):
        return self.name


class PublishedManager(models.Manager):
    """Только опубликованные материалы (дата публикации уже наступила)."""

    def get_queryset(self):
        return super().get_queryset().filter(published_at__isnull=False,
                                             published_at__lte=timezone.now())


class News(models.Model):
    """Новость клуба или история выпускника."""

    category = models.ForeignKey(NewsCategory, on_delete=models.PROTECT,
                                 verbose_name="Категория", related_name="items")
    title = models.CharField("Заголовок", max_length=200)
    summary = models.CharField("Краткое описание", max_length=300, blank=True)
    body = models.TextField("Текст")
    image = models.ImageField("Изображение", upload_to="news/", blank=True,
                              validators=[validate_image_file])
    published_at = models.DateTimeField("Дата публикации", null=True, blank=True,
                                        help_text="Пустое значение — черновик")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               null=True, verbose_name="Автор", related_name="news")

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        db_table = "news"
        verbose_name = "Публикация"
        verbose_name_plural = "Публикации"
        ordering = ["-published_at", "-id"]
        indexes = [models.Index(fields=["-published_at"], name="idx_news_pub")]

    def __str__(self):
        return self.title

    @property
    def is_draft(self):
        return self.published_at is None
