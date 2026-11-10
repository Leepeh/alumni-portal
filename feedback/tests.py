from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import Feedback


class FeedbackFormTests(TestCase):
    """Проверка формы обратной связи."""

    def setUp(self):
        self.url = reverse("feedback:contacts")
        self.data = {
            "name": "Мария",
            "email": "maria@example.ru",
            "topic": "Вступление в клуб",
            "message": "Подскажите, как долго рассматривается заявка?",
            "consent": "on",
        }

    def test_message_is_saved(self):
        response = self.client.post(self.url, self.data, follow=True)
        self.assertContains(response, "Сообщение отправлено")
        self.assertEqual(Feedback.objects.count(), 1)
        self.assertFalse(Feedback.objects.get().is_processed)

    def test_message_without_consent_is_rejected(self):
        del self.data["consent"]
        response = self.client.post(self.url, self.data)
        self.assertContains(response, "нужно согласие")
        self.assertEqual(Feedback.objects.count(), 0)

    def test_too_short_message_is_rejected(self):
        self.data["message"] = "Привет"
        response = self.client.post(self.url, self.data)
        self.assertContains(response, "Опишите вопрос подробнее")

    def test_database_rejects_record_without_consent(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Feedback.objects.create(name="А", email="a@example.ru", message="Текст", consent=False)

    def test_script_in_message_is_stored_as_text(self):
        self.data["message"] = "<script>alert('xss')</script> длинный текст"
        self.client.post(self.url, self.data)
        self.assertEqual(Feedback.objects.count(), 1)
