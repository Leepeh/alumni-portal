from django.test import TestCase
from django.urls import reverse

from .context_processors import MENU


class PublicPagesTests(TestCase):
    """Проверка публичных страниц: доступность, меню, «хлебные крошки», подвал."""

    pages = [
        "core:home", "core:about", "news:list", "events:list", "news:stories",
        "vacancies:list", "vacancies:partners", "core:gallery", "core:documents",
        "core:privacy", "feedback:contacts", "club:join", "club:join_done", "accounts:login",
    ]

    def test_at_least_ten_public_pages(self):
        self.assertGreaterEqual(len(self.pages), 10)

    def test_pages_open_for_guest(self):
        for name in self.pages:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_every_page_has_breadcrumbs_and_footer(self):
        for name in self.pages:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertContains(response, 'class="breadcrumb"')
                self.assertContains(response, "Разработка портала")

    def test_menu_has_ten_items_and_all_links_work(self):
        self.assertGreaterEqual(len(MENU), 10)
        response = self.client.get(reverse("core:home"))
        for title, route in MENU:
            with self.subTest(item=title):
                self.assertContains(response, f'href="{reverse(route)}"')
                self.assertEqual(self.client.get(reverse(route)).status_code, 200)

    def test_unknown_page_returns_404(self):
        self.assertEqual(self.client.get("/no-such-page/").status_code, 404)
