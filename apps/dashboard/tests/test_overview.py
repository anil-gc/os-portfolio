from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.certificates.models import Certificate
from apps.contact.models import Message
from apps.experience.models import Experience
from apps.portfolio.models import Profile
from apps.projects.models import Project
from apps.skills.models import Skill


class DashboardOverviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_superuser("overview-owner")
        cls.editor = get_user_model().objects.create_user("overview-editor", is_staff=True)

    def setUp(self):
        self.client.force_login(self.owner)
        self.url = reverse("dashboard:home")

    def project(self, number, **extra):
        return Project.objects.create(
            title=f"Project {number}", slug=f"project-{number}", category="Web",
            summary="Summary", description="Description", year=2026, **extra,
        )

    def message(self, number, **extra):
        return Message.objects.create(
            name=f"Sender {number}", subject=f"Subject {number}",
            email=f"private{number}@example.com", message="Private message body", **extra,
        )

    def grant(self, *codenames):
        self.editor.user_permissions.add(*Permission.objects.filter(codename__in=codenames))
        self.client.force_login(self.editor)

    def test_counts_include_real_drafts_and_unread_messages(self):
        self.project(1, is_published=True)
        self.project(2)
        Skill.objects.create(name="Python", category="Backend", is_published=True)
        Certificate.objects.create(title="Certificate", issuer="Issuer", issued_date=date(2026, 1, 1))
        Experience.objects.create(role="Developer", company="Company", start_date=date(2026, 1, 1))
        self.message(1)
        self.message(2, is_read=True)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([s["total"] for s in response.context["stats"]], [2, 1, 1, 1, 2])
        self.assertEqual(response.context["stats"][0]["detail"], "1 published · 1 draft")
        self.assertEqual(response.context["unread_messages"], 1)
        self.assertContains(response, "1 unread")

    def test_empty_database_has_zero_counts_and_useful_states(self):
        response = self.client.get(self.url)
        self.assertEqual([s["total"] for s in response.context["stats"]], [0] * 5)
        self.assertContains(response, "Your next project starts here")
        self.assertContains(response, "A quiet inbox")
        self.assertContains(response, "Set up profile")
        self.assertNotContains(response, "Edit profile")

    def test_recent_projects_use_update_time_and_deterministic_limit(self):
        projects = [self.project(i) for i in range(6)]
        now = timezone.now()
        Project.objects.update(updated_at=now - timedelta(days=1))
        Project.objects.filter(pk=projects[0].pk).update(updated_at=now)
        response = self.client.get(self.url)
        self.assertEqual([p.pk for p in response.context["recent_projects"]], [projects[i].pk for i in (0, 5, 4, 3)])

    def test_recent_messages_use_created_time_not_read_updates(self):
        messages = [self.message(i, is_read=i % 2 == 0) for i in range(6)]
        Message.objects.update(created_at=timezone.now())
        messages[0].save()
        response = self.client.get(self.url)
        self.assertEqual([m.pk for m in response.context["recent_messages"]], [m.pk for m in reversed(messages[2:])])
        self.assertContains(response, "Unread")
        self.assertContains(response, '<span class="status-badge status-draft">Read</span>', html=True)
        self.assertNotContains(response, "@example.com")
        self.assertNotContains(response, "Private message body")

    def test_content_is_escaped_and_status_and_image_are_rendered(self):
        project = self.project(1, featured=True, is_published=True, image_url="https://example.com/thumb.png")
        Project.objects.filter(pk=project.pk).update(title="<script>alert(1)</script>")
        Message.objects.create(name="<b>Sender</b>", subject="<script>bad()</script>", email="private@example.com", message="Secret")
        response = self.client.get(self.url)
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertContains(response, "&lt;b&gt;Sender&lt;/b&gt;")
        self.assertContains(response, "&lt;script&gt;bad()&lt;/script&gt;")
        self.assertContains(response, "Featured")
        self.assertContains(response, "Published")
        self.assertContains(response, 'src="https://example.com/thumb.png"')

    def test_permissionless_staff_get_no_private_content_or_edit_links(self):
        self.project(1)
        self.message(1)
        self.client.force_login(self.editor)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["stats"], [])
        self.assertEqual(response.context["quick_actions"], [])
        self.assertContains(response, "Ask your administrator")
        self.assertNotContains(response, "Project 1")
        self.assertNotContains(response, "Sender 1")

    def test_view_only_permission_allows_matching_summary_and_admin_links(self):
        project = self.project(1)
        self.message(1)
        self.grant("view_project")
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["stats"]), 1)
        self.assertContains(response, project.title)
        self.assertNotContains(response, "Recent messages")
        self.assertNotContains(response, "Add project")
        self.assertEqual(self.client.get(reverse("admin:projects_project_change", args=[project.pk])).status_code, 200)

    def test_change_permission_also_allows_reading_overview(self):
        self.project(1)
        self.grant("change_project")
        response = self.client.get(self.url)
        self.assertEqual(response.context["stats"][0]["total"], 1)
        self.assertContains(response, "Project 1")

    def test_add_only_permission_shows_action_without_private_data(self):
        self.grant("add_project")
        response = self.client.get(self.url)
        self.assertEqual(response.context["stats"], [])
        self.assertEqual([a["label"] for a in response.context["quick_actions"]], ["Add project"])
        self.assertEqual(self.client.get(response.context["quick_actions"][0]["url"]).status_code, 200)

    def test_quick_actions_and_stat_links_open_existing_admin_pages(self):
        Profile.objects.create(name="Owner", headline="Developer", bio="Bio")
        response = self.client.get(self.url)
        self.assertEqual([a["label"] for a in response.context["quick_actions"]], ["Add project", "Add skill", "Add certificate", "Edit profile"])
        for item in [*response.context["quick_actions"], *response.context["stats"]]:
            with self.subTest(url=item["url"]):
                self.assertEqual(self.client.get(item["url"]).status_code, 200)

    def test_missing_profile_links_to_setup_only_with_add_permission(self):
        self.grant("change_profile")
        self.assertEqual(self.client.get(self.url).context["quick_actions"], [])
        self.grant("add_profile")
        action = self.client.get(self.url).context["quick_actions"][0]
        self.assertEqual(action["label"], "Set up profile")
        self.assertEqual(self.client.get(action["url"]).status_code, 200)
        Profile.objects.create(name="Owner")
        self.editor.user_permissions.clear()
        self.grant("add_profile")
        self.assertEqual(self.client.get(self.url).context["quick_actions"], [])

    def test_render_uses_bounded_queries_and_does_not_fetch_message_secrets(self):
        for i in range(12):
            self.project(i)
            self.message(i)
        # Session + user, five aggregates, two bounded lists, one profile lookup.
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(queries), 10)
        message_queries = [q["sql"] for q in queries if 'FROM "contact_message"' in q["sql"]]
        self.assertEqual(len(message_queries), 2)
        for sql in message_queries:
            self.assertNotIn('"email"', sql)
            self.assertNotIn('"message"', sql)
        self.assertTrue(any("LIMIT 4" in sql for sql in message_queries))
