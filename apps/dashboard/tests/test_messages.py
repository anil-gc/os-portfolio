from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.contact.models import Message
from apps.portfolio.models import Profile


class MessageManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.owner = users.objects.create_superuser("message-owner")
        cls.staff = users.objects.create_user("message-staff", is_staff=True)
        cls.visitor = users.objects.create_user("message-visitor")
        cls.inactive = users.objects.create_user("message-inactive", is_staff=True, is_active=False)
        cls.entry = Message.objects.create(name="Private Sender", email="private@example.com", subject="Private subject", message="First line of a private message.\nSecond line.")
        Profile.objects.create(name="Owner", headline="Headline", bio="Bio")

    def setUp(self):
        cache.clear()
        self.client.force_login(self.owner)
        self.list_url = reverse("dashboard:message-list")
        self.detail_url = reverse("dashboard:message-detail", args=[self.entry.pk])
        self.status_url = reverse("dashboard:message-status", args=[self.entry.pk])
        self.delete_url = reverse("dashboard:message-delete", args=[self.entry.pk])
        self.routes = (self.list_url, self.detail_url, self.status_url, self.delete_url)

    def grant(self, *actions):
        self.staff.user_permissions.set(Permission.objects.filter(content_type__app_label="contact", codename__in=[f"{action}_message" for action in actions]))
        self.client.force_login(self.staff)

    def test_anonymous_cannot_access_or_mutate_any_route(self):
        self.client.logout()
        for url in self.routes:
            for method in (self.client.get, self.client.post):
                with self.subTest(url=url, method=method.__name__):
                    response = method(url, {"status": "read"})
                    self.assertEqual(response.status_code, 302)
                    self.assertTrue(response.url.startswith(reverse("dashboard:login")))
                    self.assertNotIn(b"private@example.com", response.content)
        self.assertTrue(Message.objects.filter(pk=self.entry.pk, is_read=False).exists())

    def test_permissionless_staff_and_nonstaff_cannot_access_even_known_ids(self):
        self.visitor.user_permissions.set(Permission.objects.filter(content_type__app_label="contact"))
        for user in (self.staff, self.visitor):
            self.client.force_login(user)
            for url in self.routes:
                for method in (self.client.get, self.client.post):
                    response = method(url, {"status": "read"})
                    self.assertEqual(response.status_code, 403)
                    self.assertNotContains(response, "Private Sender", status_code=403)
        self.assertTrue(Message.objects.filter(pk=self.entry.pk, is_read=False).exists())

    def test_inactive_staff_cannot_read_or_mutate(self):
        self.client.force_login(self.inactive)
        for url in self.routes:
            self.assertEqual(self.client.get(url).status_code, 302)
            self.assertEqual(self.client.post(url, {"status": "read"}).status_code, 302)

    def test_owner_can_open_pages_with_private_cache_headers(self):
        for url in (self.list_url, self.detail_url, self.delete_url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIn("no-store", response.headers["Cache-Control"])
            self.assertContains(response, 'name="csrfmiddlewaretoken"')
            self.assertContains(response, 'content="noindex, nofollow"')

    def test_view_only_staff_can_read_without_mutation_controls(self):
        self.grant("view")
        self.assertEqual(self.client.get(self.list_url).status_code, 200)
        response = self.client.get(self.detail_url)
        self.assertContains(response, "private@example.com")
        self.assertNotContains(response, "Mark as Read")
        self.assertNotContains(response, "Delete message")
        self.assertEqual(self.client.post(self.status_url, {"status": "read"}).status_code, 403)
        self.assertEqual(self.client.get(self.delete_url).status_code, 403)
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)

    def test_change_only_staff_can_read_and_set_status_but_not_delete(self):
        self.grant("change")
        self.assertEqual(self.client.get(self.list_url).status_code, 200)
        self.assertEqual(self.client.get(self.detail_url).status_code, 200)
        self.assertRedirects(self.client.post(self.status_url, {"status": "read"}), self.detail_url)
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)

    def test_add_or_delete_permission_alone_does_not_disclose_content(self):
        for action in ("add", "delete"):
            self.grant(action)
            for url in self.routes:
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url).status_code, 403)

    def test_view_and_delete_permission_can_confirm_delete_but_not_change_status(self):
        self.grant("view", "delete")
        self.assertEqual(self.client.get(self.delete_url).status_code, 200)
        self.assertEqual(self.client.post(self.status_url, {"status": "read"}).status_code, 403)
        self.assertRedirects(self.client.post(self.delete_url), self.list_url)

    def test_csrf_protects_status_and_delete(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for url in (self.status_url, self.delete_url):
            self.assertEqual(client.post(url, {"status": "read"}).status_code, 403)
        self.assertTrue(Message.objects.filter(pk=self.entry.pk, is_read=False).exists())

    def test_list_and_detail_get_head_have_no_side_effects(self):
        before = Message.objects.get(pk=self.entry.pk).updated_at
        for url in (self.list_url, self.detail_url, self.delete_url):
            self.assertEqual(self.client.get(url).status_code, 200)
            self.assertEqual(self.client.head(url).status_code, 200)
        self.entry.refresh_from_db()
        self.assertFalse(self.entry.is_read)
        self.assertEqual(self.entry.updated_at, before)

    def test_status_get_rejected_and_other_pages_do_not_accept_updates(self):
        self.assertEqual(self.client.get(self.status_url, {"status": "read"}).status_code, 405)
        for url in (self.list_url, self.detail_url):
            self.assertEqual(self.client.post(url, {"is_read": True, "name": "Changed"}).status_code, 405)
        self.entry.refresh_from_db()
        self.assertFalse(self.entry.is_read)
        self.assertEqual(self.entry.name, "Private Sender")

    def test_read_unread_persist_and_repeated_status_is_idempotent(self):
        before = self.entry.created_at
        for state in ("read", "read", "unread", "unread"):
            response = self.client.post(self.status_url, {"status": state, "message": "Overwrite", "name": "Overwrite"}, follow=True)
            self.assertContains(response, f"Message marked as {state}.")
            self.entry.refresh_from_db()
            self.assertEqual(self.entry.is_read, state == "read")
            self.assertEqual(self.entry.name, "Private Sender")
            self.assertIn("First line", self.entry.message)
            self.assertEqual(self.entry.created_at, before)

    def test_invalid_status_returns_useful_error_without_mutation(self):
        for data in ({}, {"status": "archived"}, {"status": "true"}):
            response = self.client.post(self.status_url, data)
            self.assertContains(response, "Choose Read or Unread.", status_code=400)
        self.entry.refresh_from_db()
        self.assertFalse(self.entry.is_read)

    def test_delete_requires_confirmation_then_post(self):
        response = self.client.get(self.delete_url)
        self.assertContains(response, "Delete this message from Private Sender?")
        self.assertContains(response, f'href="{self.detail_url}"')
        self.assertTrue(Message.objects.filter(pk=self.entry.pk).exists())
        self.assertEqual(self.client.delete(self.delete_url).status_code, 405)
        response = self.client.post(self.delete_url, follow=True)
        self.assertContains(response, "Message deleted.")
        self.assertFalse(Message.objects.filter(pk=self.entry.pk).exists())
        self.assertContains(response, "No contact messages yet.")

    def test_missing_ids_return_404_to_authorized_staff(self):
        for route in ("message-detail", "message-delete"):
            self.assertEqual(self.client.get(reverse(f"dashboard:{route}", args=[9999])).status_code, 404)
        self.assertEqual(self.client.post(reverse("dashboard:message-status", args=[9999]), {"status": "read"}).status_code, 404)
        self.assertEqual(self.client.post(reverse("dashboard:message-delete", args=[9999])).status_code, 404)

    def test_subject_sender_and_body_are_escaped(self):
        Message.objects.filter(pk=self.entry.pk).update(name="<b>Sender</b>", subject="<script>alert(1)</script>", message='<img src=x onerror="alert(1)">\nNext line')
        for url in (self.list_url, self.detail_url, self.delete_url):
            response = self.client.get(url)
            self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
            self.assertNotContains(response, "<script>alert(1)</script>")
            self.assertNotContains(response, '<img src=x onerror="alert(1)">')
        self.assertContains(self.client.get(self.detail_url), "&lt;img src=x")

    def test_list_has_concise_preview_and_detail_has_full_message(self):
        Message.objects.filter(pk=self.entry.pk).update(message="A" * 200 + "PRIVATE TAIL")
        response = self.client.get(self.list_url)
        self.assertContains(response, "A" * 100)
        self.assertNotContains(response, "PRIVATE TAIL")
        entry = response.context["entries"][0]
        self.assertIn("message", entry.get_deferred_fields())
        self.assertLessEqual(len(entry.preview), 181)
        self.assertContains(self.client.get(self.detail_url), "PRIVATE TAIL")

    def test_newest_first_and_stable_pagination(self):
        created = [Message.objects.create(name=f"Sender {i}", email=f"sender{i}@example.com", subject=f"Subject {i}", message="A test message") for i in range(12)]
        Message.objects.update(created_at=timezone.now())
        response = self.client.get(self.list_url)
        self.assertEqual(response.context["paginator"].count, 13)
        self.assertEqual([entry.pk for entry in response.context["entries"]], [entry.pk for entry in reversed(created[-10:])])
        self.assertContains(response, "Page 1 of 2")
        self.assertEqual(len(self.client.get(self.list_url, {"page": 2}).context["entries"]), 3)
        self.client.post(self.status_url, {"status": "read"})
        self.assertEqual(self.client.get(self.list_url).context["entries"][0].pk, created[-1].pk)

    def test_search_sender_email_subject_and_status_filters(self):
        read = Message.objects.create(name="Other Person", email="other@different.test", subject="Project offer", message="Distinct body", is_read=True)
        for query in ("other person", "DIFFERENT.TEST", "project offer"):
            self.assertEqual([item.pk for item in self.client.get(self.list_url, {"q": query}).context["entries"]], [read.pk])
        self.assertEqual(self.client.get(self.list_url, {"q": "Distinct body"}).context["paginator"].count, 0)
        self.assertEqual(self.client.get(self.list_url, {"status": "read"}).context["entries"][0].pk, read.pk)
        self.assertEqual(self.client.get(self.list_url, {"status": "unread"}).context["entries"][0].pk, self.entry.pk)
        self.assertEqual(self.client.get(self.list_url, {"q": "Other", "status": "unread"}).context["paginator"].count, 0)

    def test_invalid_status_filter_falls_back_to_all_and_search_is_bounded(self):
        response = self.client.get(self.list_url, {"q": "x" * 200, "status": "secret"})
        self.assertEqual(response.context["query"], "x" * 160)
        self.assertEqual(response.context["status_filter"], "")

    def test_pagination_preserves_encoded_filters(self):
        for i in range(11):
            Message.objects.create(name="A & B", email="ab@example.com", subject=str(i), message="Message preview")
        response = self.client.get(self.list_url, {"q": "A & B", "status": "unread"})
        self.assertContains(response, "q=A+%26+B&amp;status=unread&amp;page=2")

    def test_real_empty_and_filtered_empty_states(self):
        response = self.client.get(self.list_url, {"q": "missing"})
        self.assertContains(response, "No matching messages")
        Message.objects.all().delete()
        response = self.client.get(self.list_url)
        self.assertContains(response, "No contact messages yet.")
        self.assertContains(response, "0 total &middot; 0 unread")

    def test_sidebar_visibility_and_active_state(self):
        response = self.client.get(self.list_url)
        self.assertContains(response, 'href="/dashboard/messages/" aria-current="page"')
        self.client.force_login(self.staff)
        self.assertNotContains(self.client.get(reverse("dashboard:home")), 'href="/dashboard/messages/"')

    def test_overview_counts_links_and_privacy_follow_mutations(self):
        home = reverse("dashboard:home")
        response = self.client.get(home)
        self.assertContains(response, f'href="{self.list_url}"')
        self.assertContains(response, f'href="{self.detail_url}"')
        self.assertEqual(response.context["unread_messages"], 1)
        self.assertNotContains(response, "private@example.com")
        self.assertNotContains(response, "First line of a private message")
        self.client.post(self.status_url, {"status": "read"})
        self.assertEqual(self.client.get(home).context["unread_messages"], 0)
        self.client.post(self.delete_url)
        response = self.client.get(home)
        stat = next(item for item in response.context["stats"] if item["label"] == "Contact messages")
        self.assertEqual(stat["total"], 0)
        self.assertEqual(list(response.context["recent_messages"]), [])

    def test_list_queries_do_not_grow_per_message(self):
        with CaptureQueriesContext(connection) as before:
            self.client.get(self.list_url)
        for i in range(9):
            Message.objects.create(name=str(i), email="visitor@example.com", subject="Subject", message="Message content")
        with CaptureQueriesContext(connection) as after:
            self.client.get(self.list_url)
        self.assertEqual(len(before), len(after))

    def test_public_submission_appears_unread_in_same_inbox_and_detail(self):
        payload = {"name": "New Visitor", "email": "new@example.com", "subject": "New project", "message": "A message from the public form."}
        visitor = Client(enforce_csrf_checks=True)
        response = visitor.post(reverse("v1:contact:create"), payload, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"detail": "Message received."})
        entry = Message.objects.get(email="new@example.com")
        self.assertFalse(entry.is_read)
        self.assertContains(self.client.get(self.list_url), "New Visitor")
        detail = self.client.get(reverse("dashboard:message-detail", args=[entry.pk]))
        for value in payload.values():
            self.assertContains(detail, value)

    def test_public_endpoints_cannot_retrieve_private_messages(self):
        client = Client()
        contact_url = reverse("v1:contact:create")
        for url, status in ((contact_url, 405), (f"{contact_url}{self.entry.pk}/", 404)):
            response = client.get(url)
            self.assertEqual(response.status_code, status)
            self.assertNotIn(b"private@example.com", response.content)
        site = client.get(reverse("v1:portfolio:site"))
        self.assertNotIn("messages", site.json())
        self.assertNotIn(b"Private Sender", site.content)
        self.assertNotIn(b"private@example.com", site.content)
        self.assertNotIn(b"First line of a private message", site.content)
