from django.urls import reverse


def crumbs(*items):
    """Собирает «хлебные крошки» страницы.

    Каждый элемент: строка (текущая страница, без ссылки) или пара
    (название, имя маршрута). Ссылка на главную добавляется в шаблоне.
    """
    result = []
    for item in items:
        if isinstance(item, str):
            result.append({"title": item, "url": None})
        else:
            title, route, *args = item
            result.append({"title": title, "url": reverse(route, args=args)})
    return result
