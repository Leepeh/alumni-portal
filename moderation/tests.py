from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from club.models import (CONSENT_VERSION, GraduateRecord, MembershipRequest, PdConsent, Program,
                         RequestStatus)
from core.models import ActionLog
from core.testutils import PASSWORD, make_alumnus, make_moderator
from events.models import Event, EventRegistration, EventStatus
from feedback.models import Feedback
from news.models import News, NewsCategory

from .urls import SECTIONS


class ModeratorTestCase(TestCase):
    def setUp(self):
        self.moderator = make_moderator()
        self.client.login(username=self.moderator.email, password=PASSWORD)

    def make_request(self):
        return MembershipRequest.objects.create(
            last_name="Григорьева", first_name="Марина", email="marina@example.ru",
            program=Program.objects.first(), grad_year=2022,
            status=RequestStatus.objects.get(code=RequestStatus.PENDING),
            consent_version=CONSENT_VERSION)


class AccessTests(ModeratorTestCase):
    """Кабинет модератора закрыт для гостей и выпускников."""

    pages = ["moderation:home", "moderation:requests", "moderation:members", "moderation:feedback",
             "moderation:responses"] + [section.route("list") for section in SECTIONS]

    def test_at_least_five_pages_open_for_moderator(self):
        self.assertGreaterEqual(len(self.pages), 5)
        for name in self.pages:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'class="breadcrumb"')

    def test_alumnus_gets_403(self):
        self.client.logout()
        alumnus = make_alumnus()
        self.client.login(username=alumnus.email, password=PASSWORD)
        for name in self.pages:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 403)

    def test_guest_is_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("moderation:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)


class MembershipRequestTests(ModeratorTestCase):
    """Рассмотрение заявок на вступление."""

    def test_approve_creates_account_profile_and_consent(self):
        item = self.make_request()
        url = reverse("moderation:request_detail", args=[item.pk])
        response = self.client.post(url, {"approve": "1"}, follow=True)
        self.assertContains(response, "временный пароль")
        user = User.objects.get(email="marina@example.ru")
        self.assertTrue(user.is_alumnus)
        self.assertEqual(user.alumni_profile.grad_year, 2022)
        self.assertEqual(PdConsent.objects.get(user=user).version, CONSENT_VERSION)
        item.refresh_from_db()
        self.assertEqual(item.status.code, RequestStatus.APPROVED)
        self.assertEqual(item.reviewed_by, self.moderator)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(ActionLog.objects.filter(action__startswith="Одобрение").exists())

    def test_reject_requires_comment(self):
        item = self.make_request()
        url = reverse("moderation:request_detail", args=[item.pk])
        self.client.post(url, {"reject": "1", "comment": ""})
        item.refresh_from_db()
        self.assertEqual(item.status.code, RequestStatus.PENDING)
        self.client.post(url, {"reject": "1", "comment": "Нет в реестре"})
        item.refresh_from_db()
        self.assertEqual(item.status.code, RequestStatus.REJECTED)
        self.assertFalse(User.objects.filter(email=item.email).exists())

    def test_reviewed_request_cannot_be_approved_again(self):
        item = self.make_request()
        url = reverse("moderation:request_detail", args=[item.pk])
        self.client.post(url, {"approve": "1"})
        self.client.post(url, {"approve": "1"})
        self.assertEqual(User.objects.filter(email=item.email).count(), 1)

    def test_registry_match_is_shown(self):
        item = self.make_request()
        url = reverse("moderation:request_detail", args=[item.pk])
        self.assertContains(self.client.get(url), "совпадений по фамилии")
        GraduateRecord.objects.create(last_name="Григорьева", first_name="Марина",
                                      program=item.program, grad_year=2022)
        self.assertContains(self.client.get(url), "Найден в реестре выпускников")


class ContentTests(ModeratorTestCase):
    """Управление публикациями, мероприятиями и обращениями."""

    def test_created_news_gets_author(self):
        category = NewsCategory.objects.get(code=NewsCategory.NEWS)
        self.client.post(reverse("moderation:news_add"), {
            "category": category.pk, "title": "Новая новость", "body": "Текст новости"})
        news = News.objects.get(title="Новая новость")
        self.assertEqual(news.author, self.moderator)
        self.assertTrue(news.is_draft)

    def test_news_can_be_edited_and_deleted(self):
        category = NewsCategory.objects.get(code=NewsCategory.NEWS)
        news = News.objects.create(category=category, title="Старый заголовок", body="Текст")
        self.client.post(reverse("moderation:news_edit", args=[news.pk]), {
            "category": category.pk, "title": "Новый заголовок", "body": "Текст"})
        news.refresh_from_db()
        self.assertEqual(news.title, "Новый заголовок")
        self.client.post(reverse("moderation:news_delete", args=[news.pk]))
        self.assertFalse(News.objects.filter(pk=news.pk).exists())

    def test_capacity_cannot_be_less_than_registrations(self):
        status = EventStatus.objects.get(code=EventStatus.OPEN)
        event = Event.objects.create(title="Встреча", capacity=5, status=status,
                                     start_at=timezone.now() + timedelta(days=3))
        for number in range(2):
            alumnus = make_alumnus(f"a{number}@example.ru")
            EventRegistration.objects.create(event=event, profile=alumnus.alumni_profile)
        response = self.client.post(reverse("moderation:events_edit", args=[event.pk]), {
            "title": "Встреча", "start_at": "2030-01-01T18:00", "capacity": 1,
            "status": status.pk})
        self.assertContains(response, "не может быть меньше")

    def test_attendance_mark_is_toggled(self):
        status = EventStatus.objects.get(code=EventStatus.FINISHED)
        event = Event.objects.create(title="Встреча", capacity=5, status=status,
                                     start_at=timezone.now() - timedelta(days=3))
        registration = EventRegistration.objects.create(
            event=event, profile=make_alumnus().alumni_profile)
        self.client.post(reverse("moderation:toggle_attendance", args=[registration.pk]))
        registration.refresh_from_db()
        self.assertTrue(registration.attended)

    def test_feedback_answer_marks_processed(self):
        item = Feedback.objects.create(name="Мария", email="m@example.ru",
                                       message="Вопрос о вступлении", consent=True)
        self.client.post(reverse("moderation:feedback_detail", args=[item.pk]),
                         {"answer": "Заявка рассматривается два дня."})
        item.refresh_from_db()
        self.assertTrue(item.is_processed)
        self.assertEqual(item.processed_by, self.moderator)
        self.assertEqual(len(mail.outbox), 1)


class MemberListTests(ModeratorTestCase):
    """Реестр членов клуба в кабинете модератора."""

    def setUp(self):
        super().setUp()
        self.first = make_alumnus("ivanov@example.ru", "Иванов", "Пётр")
        self.second = make_alumnus("smirnova@example.ru", "Смирнова", "Ольга")

    def test_all_members_are_listed(self):
        response = self.client.get(reverse("moderation:members"))
        self.assertContains(response, "Иванов Пётр")
        self.assertContains(response, "Смирнова Ольга")

    def test_search_by_last_name_and_email(self):
        response = self.client.get(reverse("moderation:members"), {"q": "иванов"})
        self.assertContains(response, "Иванов Пётр")
        self.assertNotContains(response, "Смирнова Ольга")
        response = self.client.get(reverse("moderation:members"), {"q": "smirnova@"})
        self.assertContains(response, "Смирнова Ольга")

    def test_filter_by_faculty(self):
        other = Program.objects.exclude(faculty=self.first.alumni_profile.program.faculty).first()
        profile = self.second.alumni_profile
        profile.program = other
        profile.save()
        response = self.client.get(reverse("moderation:members"), {"faculty": other.faculty_id})
        self.assertContains(response, "Смирнова Ольга")
        self.assertNotContains(response, "Иванов Пётр")

    def test_disabled_accounts_are_hidden(self):
        self.second.is_active = False
        self.second.save()
        response = self.client.get(reverse("moderation:members"))
        self.assertNotContains(response, "Смирнова Ольга")
