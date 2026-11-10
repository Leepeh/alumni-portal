from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.testutils import PASSWORD, make_alumnus, make_moderator

from .models import Event, EventRegistration, EventStatus


class EventRegistrationTests(TestCase):
    """Проверка регистрации на мероприятие и контроля числа мест."""

    def setUp(self):
        self.alumnus = make_alumnus()
        self.event = Event.objects.create(
            title="Встреча выпускников", start_at=timezone.now() + timedelta(days=7),
            place="Главный корпус", capacity=1,
            status=EventStatus.objects.get(code=EventStatus.OPEN))
        self.register_url = reverse("events:register", args=[self.event.pk])

    def login(self, user):
        self.client.login(username=user.email, password=PASSWORD)

    def test_alumnus_registers_for_event(self):
        self.login(self.alumnus)
        self.client.post(self.register_url)
        self.assertEqual(self.event.registrations.count(), 1)
        self.assertEqual(self.event.free_places(), 0)

    def test_no_registration_without_free_places(self):
        other = make_alumnus("other@example.ru", "Другой", "Пётр")
        EventRegistration.objects.create(event=self.event, profile=other.alumni_profile)
        self.login(self.alumnus)
        response = self.client.post(self.register_url, follow=True)
        self.assertContains(response, "Свободных мест нет")
        self.assertEqual(self.event.registrations.count(), 1)

    def test_repeated_registration_is_not_duplicated(self):
        self.event.capacity = 5
        self.event.save()
        self.login(self.alumnus)
        self.client.post(self.register_url)
        self.client.post(self.register_url)
        self.assertEqual(self.event.registrations.count(), 1)

    def test_guest_is_redirected_to_login(self):
        response = self.client.post(self.register_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
        self.assertEqual(self.event.registrations.count(), 0)

    def test_moderator_cannot_register(self):
        self.login(make_moderator())
        response = self.client.post(self.register_url)
        self.assertEqual(response.status_code, 403)

    def test_registration_closed_for_finished_event(self):
        self.event.status = EventStatus.objects.get(code=EventStatus.FINISHED)
        self.event.save()
        self.login(self.alumnus)
        response = self.client.post(self.register_url, follow=True)
        self.assertContains(response, "Регистрация на это мероприятие закрыта")
        self.assertEqual(self.event.registrations.count(), 0)

    def test_cancel_registration_frees_place(self):
        self.login(self.alumnus)
        self.client.post(self.register_url)
        self.client.post(reverse("events:cancel", args=[self.event.pk]))
        self.assertEqual(self.event.free_places(), 1)

    def test_get_request_to_register_is_rejected(self):
        self.login(self.alumnus)
        self.assertEqual(self.client.get(self.register_url).status_code, 405)
