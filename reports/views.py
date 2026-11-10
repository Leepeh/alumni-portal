from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from accounts.decorators import role_required
from accounts.models import Role
from core.audit import log_action
from events.models import Event

from . import services


def _attachment(content_type, filename):
    response = HttpResponse(content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@role_required(Role.MODERATOR, Role.ADMIN)
def participants_xlsx(request, pk):
    """Выгрузка списка участников мероприятия в .xlsx."""
    event = get_object_or_404(Event, pk=pk)
    response = _attachment(services.XLSX_TYPE, f"event_{pk}_participants.xlsx")
    services.participants_workbook(event).save(response)
    log_action(request, "Выгрузка участников мероприятия в .xlsx", event)
    return response


@role_required(Role.ADMIN)
def members_xlsx(request):
    """Выгрузка реестра членов клуба в .xlsx."""
    response = _attachment(services.XLSX_TYPE, "club_members.xlsx")
    services.members_workbook().save(response)
    log_action(request, "Выгрузка реестра членов клуба в .xlsx")
    return response
