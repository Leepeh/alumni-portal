from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Пропускает пользователя только с одной из указанных ролей.

    Неавторизованный пользователь отправляется на страницу входа,
    авторизованный с другой ролью получает ответ 403.
    """
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role.code not in roles:
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
