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

    def test_required_fields_cannot_be_missing_or_blank(self):
        for field in ("name", "email", "subject", "message"):
            for value in (None, "", "   "):
                with self.subTest(field=field, value=value):
                    cache.clear()
                    payload = self.payload.copy()
                    if value is None:
                        payload.pop(field)
                    else:
                        payload[field] = value
                    response = self.client.post(self.url, payload)
                    self.assertEqual(response.status_code, 400)
                    self.assertIn(field, response.json())
        self.assertEqual(Message.objects.count(), 0)

    def test_length_limits_match_the_public_form(self):
        for field, value in (("name", "a" * 101), ("email", "a" * 245 + "@example.com"), ("subject", "a" * 161), ("message", "a" * 5001), ("message", "too short")):
            cache.clear()
            response = self.client.post(self.url, self.payload | {field: value})
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.json())
        self.assertEqual(Message.objects.count(), 0)

    def test_exact_message_length_boundaries_are_valid(self):
        for length in (10, 5000):
            self.assertEqual(self.client.post(self.url, self.payload | {"message": "a" * length}).status_code, 201)

    def test_public_submission_cannot_set_private_status_or_return_content(self):
        response = self.client.post(self.url, self.payload | {"is_read": True, "id": 9999})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"detail": "Message received."})
        self.assertFalse(Message.objects.get().is_read)
        self.assertNotEqual(Message.objects.get().pk, 9999)

    def test_public_api_has_no_update_or_delete_methods(self):
        for method in (self.client.put, self.client.patch, self.client.delete):
            self.assertEqual(method(self.url, self.payload, content_type="application/json").status_code, 405)
