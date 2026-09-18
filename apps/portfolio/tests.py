from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
from apps.projects.models import Project
from .models import Profile


class PublicPortfolioTests(TestCase):
    def setUp(self):
        Profile.objects.create(name="Test Author", headline="Developer", bio="About")
        self.project = Project.objects.create(title="Visible", slug="visible", category="Web", summary="Summary", description="Description", year=2026, is_published=True)
        Project.objects.create(title="Private", slug="private", category="Web", summary="Draft", description="Draft", year=2026)

    def test_snapshot_does_not_leak_unpublished_content(self):
        response = self.client.get(reverse("v1:portfolio:site"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p["slug"] for p in response.json()["projects"]], ["visible"])
        self.assertIsNone(response.json()["resume"])

    def test_project_list_is_read_only_and_excludes_drafts(self):
        url = reverse("v1:projects:list")
        self.assertEqual(len(self.client.get(url).json()), 1)
        self.assertEqual(self.client.post(url, {}).status_code, 405)

    def test_admin_changes_are_visible_in_next_response(self):
        self.project.title = "Updated"
        self.project.save()
        self.assertEqual(self.client.get(reverse("v1:portfolio:site")).json()["projects"][0]["title"], "Updated")

    def test_seed_cannot_overwrite_existing_content(self):
        with self.assertRaises(CommandError):
            call_command("seed_portfolio", "unused.json", stdout=StringIO())

    def test_missing_profile_returns_404(self):
        Profile.objects.all().delete()
        self.assertEqual(self.client.get(reverse("v1:portfolio:site")).status_code, 404)
