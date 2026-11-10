from django.conf import settings

# Пункты верхнего меню: (название, имя маршрута)
MENU = [
    ("Главная", "core:home"),
    ("О клубе", "core:about"),
    ("Новости", "news:list"),
    ("Мероприятия", "events:list"),
    ("Истории", "news:stories"),
    ("Вакансии", "vacancies:list"),
    ("Партнёры", "vacancies:partners"),
    ("Галерея", "core:gallery"),
    ("Документы", "core:documents"),
    ("Контакты", "feedback:contacts"),
]


def site(request):
    """Общие данные для всех шаблонов: меню, название портала, автор."""
    return {
        "menu": MENU,
        "portal_name": settings.PORTAL_NAME,
        "portal_author": settings.PORTAL_AUTHOR,
    }
