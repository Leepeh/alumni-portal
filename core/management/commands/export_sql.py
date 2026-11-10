"""Выгрузка базы данных в SQL-файл для размещения в репозитории.

Для SQLite формируется полный скрипт (структура и данные). Для PostgreSQL
используется штатная утилита: pg_dump --no-owner "$DATABASE_URL" > db/alumni_portal.sql
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Сохраняет структуру и данные базы в SQL-файл"

    def add_arguments(self, parser):
        parser.add_argument("--output", default="db/alumni_portal_demo.sql",
                            help="путь к файлу относительно корня проекта")

    def handle(self, *args, **options):
        if connection.vendor != "sqlite":
            raise CommandError("Для PostgreSQL используйте pg_dump (см. описание команды).")
        target = Path(settings.BASE_DIR) / options["output"]
        connection.ensure_connection()
        lines = list(connection.connection.iterdump())
        target.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        tables = sum(1 for line in lines if line.startswith("CREATE TABLE"))
        self.stdout.write(self.style.SUCCESS(
            f"Сохранено: {target.name}, таблиц {tables}, строк скрипта {len(lines)}."))
