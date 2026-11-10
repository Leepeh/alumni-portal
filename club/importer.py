"""Импорт реестра выпускников из файла .xlsx, выгруженного из учётной системы.

Формат файла: первая строка — заголовки, далее по одной записи в строке.
Столбцы: Фамилия, Имя, Отчество, Код направления, Год выпуска.
Импорт выполняется в одной транзакции: если хотя бы в одной строке есть ошибка,
в базу не попадает ничего, а в протоколе перечисляются строки с ошибками.
"""
from dataclasses import dataclass, field

from django.db import transaction
from django.utils import timezone
from openpyxl import Workbook, load_workbook

from .models import GraduateRecord, Program

COLUMNS = ["Фамилия", "Имя", "Отчество", "Код направления", "Год выпуска"]
MAX_ROWS = 2000


@dataclass
class ImportResult:
    """Протокол импорта."""

    created: int = 0
    updated: int = 0
    errors: list = field(default_factory=list)

    @property
    def ok(self):
        return not self.errors


class ImportRollback(Exception):
    """Служебное исключение для отмены транзакции при ошибках в строках."""


def template_workbook():
    """Пустой шаблон файла импорта с примером заполнения."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Выпускники"
    sheet.append(COLUMNS)
    sheet.append(["Иванова", "Мария", "Петровна", "38.03.05", 2022])
    return workbook


def _clean(value):
    return str(value).strip() if value is not None else ""


def _parse_row(number, row, programs):
    """Проверяет строку и возвращает данные записи или текст ошибки."""
    last_name, first_name, middle_name, code, year = (list(row) + [None] * 5)[:5]
    last_name, first_name, middle_name = _clean(last_name), _clean(first_name), _clean(middle_name)
    if not last_name or not first_name:
        return None, f"Строка {number}: не указаны фамилия или имя."
    program = programs.get(_clean(code))
    if program is None:
        return None, f"Строка {number}: направление с кодом «{_clean(code)}» не найдено в справочнике."
    try:
        year = int(year)
    except (TypeError, ValueError):
        return None, f"Строка {number}: год выпуска должен быть числом."
    if not 1990 <= year <= timezone.now().year:
        return None, f"Строка {number}: год выпуска {year} вне допустимого диапазона."
    return {"last_name": last_name, "first_name": first_name, "middle_name": middle_name,
            "program": program, "grad_year": year}, None


def import_graduates(file):
    """Загружает реестр выпускников из файла .xlsx и возвращает протокол импорта."""
    result = ImportResult()
    try:
        sheet = load_workbook(file, read_only=True, data_only=True).active
    except Exception:
        result.errors.append("Файл не удалось прочитать. Нужен файл формата .xlsx.")
        return result

    rows = list(sheet.iter_rows(values_only=True))
    if not rows or [_clean(cell) for cell in rows[0][:5]] != COLUMNS:
        result.errors.append("Заголовки столбцов не совпадают с шаблоном: " + ", ".join(COLUMNS))
        return result
    data_rows = [row for row in rows[1:] if any(cell not in (None, "") for cell in row)]
    if len(data_rows) > MAX_ROWS:
        result.errors.append(f"В файле больше {MAX_ROWS} строк. Разделите его на части.")
        return result

    # Справочник направлений читается один раз, а не для каждой строки
    programs = {program.code: program for program in Program.objects.all()}
    try:
        with transaction.atomic():
            for number, row in enumerate(data_rows, start=2):
                data, error = _parse_row(number, row, programs)
                if error:
                    result.errors.append(error)
                    continue
                _, created = GraduateRecord.objects.update_or_create(**data)
                if created:
                    result.created += 1
                else:
                    result.updated += 1
            if result.errors:
                raise ImportRollback
    except ImportRollback:
        result.created = result.updated = 0
    return result
