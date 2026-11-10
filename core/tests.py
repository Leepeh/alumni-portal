from django.test import TestCase
from django.urls import reverse


class PublicPagesTests(TestCase):
    """Проверка публичных страниц: доступность, меню, «хлебные крошки», подвал."""

    pages = ["core:home", "core:about", "club:join", "club:join_done", "accounts:login"]

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
