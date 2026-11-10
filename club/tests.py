from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import MembershipRequest, Program, RequestStatus


class JoinFormTests(TestCase):
    """Проверка подачи заявки на вступление в клуб."""

    def setUp(self):
        self.program = Program.objects.first()
        self.data = {
            "last_name": "Тестова",
            "first_name": "Анна",
            "email": "Anna@Example.ru",
            "program": self.program.pk,
            "grad_year": 2020,
            "consent": "on",
        }

    def test_request_saved_with_pending_status(self):
        response = self.client.post(reverse("club:join"), self.data)
        self.assertRedirects(response, reverse("club:join_done"))
        saved = MembershipRequest.objects.get()
        self.assertEqual(saved.status.code, RequestStatus.PENDING)
        self.assertEqual(saved.email, "anna@example.ru")
        self.assertTrue(saved.consent_version)

    def test_request_rejected_without_consent(self):
        del self.data["consent"]
        response = self.client.post(reverse("club:join"), self.data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Без согласия")
        self.assertEqual(MembershipRequest.objects.count(), 0)

    def test_duplicate_pending_request_rejected(self):
        self.client.post(reverse("club:join"), self.data)
        response = self.client.post(reverse("club:join"), self.data)
        self.assertContains(response, "уже подана")
        self.assertEqual(MembershipRequest.objects.count(), 1)

    def test_existing_member_cannot_apply_again(self):
        User.objects.create_user("anna@example.ru", "pass-12345")
        response = self.client.post(reverse("club:join"), self.data)
        self.assertContains(response, "уже состоит в клубе")

    def test_future_graduation_year_rejected(self):
        self.data["grad_year"] = 2099
        response = self.client.post(reverse("club:join"), self.data)
        self.assertContains(response, "не может быть позже")
