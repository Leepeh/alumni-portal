from .models import ActionLog


def log_action(request, action, obj=None):
    """Записывает действие пользователя в журнал.

    В журнал попадают действия модератора и администратора, которые меняют
    данные портала: рассмотрение заявок, публикации, импорт, смена ролей.
    """
    user = request.user if request.user.is_authenticated else None
    ActionLog.objects.create(
        user=user,
        action=action,
        object_repr=str(obj)[:200] if obj is not None else "",
        ip_address=request.META.get("REMOTE_ADDR"),
    )
