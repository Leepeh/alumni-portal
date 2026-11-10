import datetime

from django import template
from django.utils import timezone
from django.utils.formats import date_format

register = template.Library()


@register.filter
def attr(obj, path):
    """Возвращает значение атрибута по пути вида «partner.name» в удобном для таблицы виде."""
    value = obj
    for part in path.split("."):
        value = getattr(value, part, None)
        if callable(value):
            value = value()
        if value is None:
            return "—"
    if isinstance(value, bool):
        return "Да" if value else "Нет"
    if isinstance(value, datetime.datetime):
        return date_format(timezone.localtime(value), "d.m.Y H:i")
    if isinstance(value, datetime.date):
        return date_format(value, "d.m.Y")
    return "—" if value == "" else value


@register.simple_tag(takes_context=True)
def active(context, prefix):
    """Класс active для пункта бокового меню, если адрес страницы начинается с prefix."""
    return "active" if context["request"].path.startswith(prefix) else ""
