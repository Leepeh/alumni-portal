from django.conf import settings
from django.db import models

from .validators import validate_document_file, validate_image_file


class GalleryPhoto(models.Model):
    """Фотография в галерее клуба."""

    title = models.CharField("Подпись", max_length=200)
    image = models.ImageField("Фотография", upload_to="gallery/",
                              validators=[validate_image_file])
    taken_at = models.DateField("Дата съёмки", null=True, blank=True)
    uploaded_at = models.DateTimeField("Дата загрузки", auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, verbose_name="Кто загрузил",
                                    related_name="gallery_photos")

    class Meta:
        db_table = "gallery_photos"
        verbose_name = "Фотография галереи"
        verbose_name_plural = "Фотографии галереи"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title


class ClubDocument(models.Model):
    """Документ клуба, доступный для скачивания (положение, политика, памятка)."""

    title = models.CharField("Название", max_length=200)
    description = models.CharField("Описание", max_length=300, blank=True)
    file = models.FileField("Файл", upload_to="documents/",
                            validators=[validate_document_file])
    uploaded_at = models.DateTimeField("Дата размещения", auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, verbose_name="Кто разместил",
                                    related_name="club_documents")

    class Meta:
        db_table = "club_documents"
        verbose_name = "Документ клуба"
        verbose_name_plural = "Документы клуба"
        ordering = ["title"]

    def __str__(self):
        return self.title

    @property
    def size_kb(self):
        try:
            return max(self.file.size // 1024, 1)
        except (FileNotFoundError, ValueError):
            return None
