from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from .models import Message


class ContactTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("v1:contact:create")
        self.payload = {"name": "Visitor", "email": "visitor@example.com", "subject": "A project", "message": "Let's discuss a project."}

    def test_message_is_saved_without_public_read_access(self):
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 201)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_invalid_email_and_honeypot_are_rejected(self):
        self.assertEqual(self.client.post(self.url, self.payload | {"email": "invalid"}).status_code, 400)
        self.assertEqual(self.client.post(self.url, self.payload | {"website": "spam"}).status_code, 400)
        self.assertEqual(Message.objects.count(), 0)

    def test_rate_limit_rejects_sixth_message(self):
        for _ in range(5):
            self.assertEqual(self.client.post(self.url, self.payload).status_code, 201)
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 429)
        self.assertEqual(Message.objects.count(), 5)
