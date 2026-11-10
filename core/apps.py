import re
from functools import lru_cache

from django.apps import AppConfig
from django.db.backends.signals import connection_created


@lru_cache(maxsize=256)
def _like_regex(pattern, escape):
    """Переводит шаблон оператора LIKE в регулярное выражение без учёта регистра."""
    parts, index = [], 0
    while index < len(pattern):
        char = pattern[index]
        if escape and char == escape and index + 1 < len(pattern):
            parts.append(re.escape(pattern[index + 1]))
            index += 2
            continue
        parts.append(".*" if char == "%" else "." if char == "_" else re.escape(char))
        index += 1
    return re.compile("".join(parts), re.IGNORECASE | re.DOTALL)


def unicode_like(pattern, value, escape=None):
    """Замена встроенной функции LIKE в SQLite.

    Встроенный LIKE в SQLite не различает регистр только для латиницы, поэтому поиск
    «иванов» не находил «Иванов». В PostgreSQL такой проблемы нет.
    """
    if pattern is None or value is None:
        return None
    return _like_regex(str(pattern), escape).fullmatch(str(value)) is not None


def setup_sqlite(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        connection.connection.create_function("like", 2, unicode_like, deterministic=True)
        connection.connection.create_function("like", 3, unicode_like, deterministic=True)


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Общие компоненты портала"

    def ready(self):
        connection_created.connect(setup_sqlite)
