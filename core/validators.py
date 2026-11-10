import os

from django.conf import settings
from django.core.exceptions import ValidationError

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
DOCUMENT_EXTENSIONS = (".pdf", ".doc", ".docx", ".rtf", ".odt")


def validate_file_size(file):
    """Отклоняет файлы больше допустимого размера (5 МБ)."""
    if file.size > settings.MAX_UPLOAD_SIZE:
        limit_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
        raise ValidationError(f"Размер файла не должен превышать {limit_mb} МБ.")


def _check_extension(file, allowed):
    extension = os.path.splitext(file.name)[1].lower()
    if extension not in allowed:
        raise ValidationError("Недопустимый тип файла. Разрешены: " + ", ".join(allowed))


def validate_image_file(file):
    """Проверка загружаемой фотографии: тип и размер."""
    _check_extension(file, IMAGE_EXTENSIONS)
    validate_file_size(file)


def validate_document_file(file):
    """Проверка загружаемого документа (резюме, положение): тип и размер."""
    _check_extension(file, DOCUMENT_EXTENSIONS)
    validate_file_size(file)
