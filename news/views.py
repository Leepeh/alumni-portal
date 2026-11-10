from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from core.breadcrumbs import crumbs

from .models import News, NewsCategory

PAGE_SIZE = 6


def _paginate(request, queryset):
    return Paginator(queryset, PAGE_SIZE).get_page(request.GET.get("page"))


def news_list(request):
    """Список новостей клуба с поиском по заголовку и тексту."""
    query = request.GET.get("q", "").strip()
    items = News.published.filter(category__code=NewsCategory.NEWS)
    if query:
        # Поиск выполняется через ORM, строка запроса передаётся параметром
        items = items.filter(Q(title__icontains=query) | Q(body__icontains=query))
    return render(request, "news/list.html", {
        "page": _paginate(request, items),
        "query": query,
        "heading": "Новости клуба",
        "detail_route": "news:detail",
        "show_search": True,
        "crumbs": crumbs("Новости"),
    })


def news_detail(request, pk):
    """Страница одной новости."""
    item = get_object_or_404(News.published, pk=pk, category__code=NewsCategory.NEWS)
    return render(request, "news/detail.html", {
        "item": item,
        "crumbs": crumbs(("Новости", "news:list"), item.title),
    })


def story_list(request):
    """Истории выпускников."""
    items = News.published.filter(category__code=NewsCategory.STORY)
    return render(request, "news/list.html", {
        "page": _paginate(request, items),
        "heading": "Истории выпускников",
        "detail_route": "news:story_detail",
        "show_search": False,
        "crumbs": crumbs("Истории"),
    })


def story_detail(request, pk):
    """Страница одной истории выпускника."""
    item = get_object_or_404(News.published, pk=pk, category__code=NewsCategory.STORY)
    return render(request, "news/detail.html", {
        "item": item,
        "crumbs": crumbs(("Истории", "news:stories"), item.title),
    })
