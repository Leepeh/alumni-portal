from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import News, NewsCategory


class NewsTests(TestCase):
    """Проверка списка новостей, черновиков и поиска."""

    def setUp(self):
        news = NewsCategory.objects.get(code=NewsCategory.NEWS)
        story = NewsCategory.objects.get(code=NewsCategory.STORY)
        now = timezone.now()
        self.published = News.objects.create(category=news, title="День карьеры прошёл успешно",
                                             body="Текст новости", published_at=now)
        self.draft = News.objects.create(category=news, title="Черновик новости", body="Текст")
        self.future = News.objects.create(category=news, title="Отложенная новость", body="Текст",
                                          published_at=now + timedelta(days=3))
        self.story = News.objects.create(category=story, title="Путь аналитика",
                                         body="История", published_at=now)

    def test_list_shows_only_published_news(self):
        response = self.client.get(reverse("news:list"))
        self.assertContains(response, self.published.title)
        self.assertNotContains(response, self.draft.title)
        self.assertNotContains(response, self.future.title)
        self.assertNotContains(response, self.story.title)

    def test_draft_detail_returns_404(self):
        response = self.client.get(reverse("news:detail", args=[self.draft.pk]))
        self.assertEqual(response.status_code, 404)

    def test_stories_page_shows_only_stories(self):
        response = self.client.get(reverse("news:stories"))
        self.assertContains(response, self.story.title)
        self.assertNotContains(response, self.published.title)

    def test_search_finds_by_title(self):
        response = self.client.get(reverse("news:list"), {"q": "карьеры"})
        self.assertContains(response, self.published.title)

    def test_search_treats_sql_injection_as_text(self):
        response = self.client.get(reverse("news:list"), {"q": "' OR 1=1 --"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.published.title)

    def test_search_escapes_script_in_query(self):
        response = self.client.get(reverse("news:list"), {"q": "<script>alert(1)</script>"})
        self.assertNotContains(response, "<script>alert(1)</script>")
