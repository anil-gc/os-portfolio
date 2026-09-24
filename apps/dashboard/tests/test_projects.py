from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse

from apps.portfolio.models import Profile
from apps.projects.models import Project


class ProjectManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.owner = users.objects.create_superuser("project-owner")
        cls.staff = users.objects.create_user("project-staff", is_staff=True)
        cls.visitor = users.objects.create_user("project-visitor")
        cls.inactive = users.objects.create_user("project-inactive", is_staff=True, is_active=False)
        cls.project = Project.objects.create(
            title="Existing project", slug="existing", category="Web", summary="Summary",
            description="Full description", year=2026, technologies=["React", "Python"],
            image_url="https://example.com/original.png", is_published=True,
        )
        Profile.objects.create(name="Owner", headline="Developer", bio="Bio")

    def setUp(self):
        self.client.force_login(self.owner)
        self.list_url = reverse("dashboard:project-list")
        self.create_url = reverse("dashboard:project-create")
        self.edit_url = reverse("dashboard:project-update", args=[self.project.pk])
        self.delete_url = reverse("dashboard:project-delete", args=[self.project.pk])

    def payload(self, **overrides):
        return {
            "title": "New work", "slug": "new-work", "category": "Full stack", "year": "2026",
            "summary": "New summary", "description": "New description", "technologies": "Django\nReact",
            "image_url": "https://example.com/new.png", "source_url": "https://github.com/example/project",
            "live_url": "https://example.com/demo", "accent": "green", "sort_order": "3",
            "featured": "on", "is_published": "on", **overrides,
        }

    def grant(self, *permissions):
        self.staff.user_permissions.set(Permission.objects.filter(codename__in=permissions, content_type__app_label="projects"))
        self.client.force_login(self.staff)

    def public_slugs(self, url_name):
        response = self.client.get(reverse(url_name))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        return [p["slug"] for p in data["projects"]] if isinstance(data, dict) else [p["slug"] for p in data]

    def test_anonymous_cannot_get_or_post_any_management_route(self):
        self.client.logout()
        for url in (self.list_url, self.create_url, self.edit_url, self.delete_url):
            for method in (self.client.get, self.client.post):
                with self.subTest(url=url, method=method.__name__):
                    response = method(url, self.payload())
                    self.assertEqual(response.status_code, 302)
                    self.assertTrue(response.url.startswith(reverse("dashboard:login")))
        self.assertEqual(Project.objects.count(), 1)

    def test_nonstaff_and_permissionless_staff_cannot_read_or_mutate(self):
        self.visitor.user_permissions.set(Permission.objects.filter(content_type__app_label="projects"))
        for user in (self.visitor, self.staff):
            self.client.force_login(user)
            for url in (self.list_url, self.create_url, self.edit_url, self.delete_url):
                for method in (self.client.get, self.client.post):
                    with self.subTest(user=user.username, url=url, method=method.__name__):
                        self.assertEqual(method(url, self.payload()).status_code, 403)
        self.assertEqual(Project.objects.get().title, "Existing project")

    def test_inactive_staff_cannot_use_management(self):
        self.client.force_login(self.inactive)
        self.assertEqual(self.client.get(self.list_url).status_code, 302)
        self.assertEqual(self.client.post(self.delete_url).status_code, 302)
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

    def test_owner_can_open_all_pages_and_responses_are_private(self):
        for url in (self.list_url, self.create_url, self.edit_url, self.delete_url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIn("no-store", response.headers["Cache-Control"])
            self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_view_permission_does_not_grant_mutations(self):
        self.grant("view_project")
        response = self.client.get(self.list_url)
        self.assertContains(response, "Existing project")
        for url in (self.create_url, self.edit_url, self.delete_url):
            self.assertNotContains(response, f'href="{url}"')
            self.assertEqual(self.client.post(url, self.payload()).status_code, 403)

    def test_add_only_staff_can_create_and_return_to_accessible_page(self):
        self.grant("add_project")
        self.assertEqual(self.client.get(self.create_url).status_code, 200)
        response = self.client.post(self.create_url, self.payload())
        self.assertRedirects(response, reverse("dashboard:home"))
        self.assertEqual(self.client.get(self.list_url).status_code, 403)
        self.assertTrue(Project.objects.filter(slug="new-work").exists())

    def test_change_permission_does_not_grant_add_or_delete(self):
        self.grant("change_project")
        self.assertEqual(self.client.get(self.list_url).status_code, 200)
        self.assertRedirects(self.client.post(self.edit_url, self.payload()), self.list_url)
        self.assertEqual(self.client.post(self.create_url, self.payload()).status_code, 403)
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)

    def test_delete_only_staff_can_confirm_delete_and_return_home(self):
        self.grant("delete_project")
        self.assertEqual(self.client.get(self.delete_url).status_code, 200)
        self.assertRedirects(self.client.post(self.delete_url), reverse("dashboard:home"))
        self.assertEqual(Project.objects.count(), 0)

    def test_valid_create_saves_every_existing_field_and_public_data(self):
        response = self.client.post(self.create_url, self.payload(), follow=True)
        self.assertContains(response, 'Project &quot;New work&quot; created.')
        project = Project.objects.get(slug="new-work")
        for field, expected in {
            "title": "New work", "category": "Full stack", "year": 2026,
            "summary": "New summary", "description": "New description",
            "technologies": ["Django", "React"], "image_url": "https://example.com/new.png",
            "source_url": "https://github.com/example/project", "live_url": "https://example.com/demo",
            "accent": "green", "sort_order": 3, "featured": True, "is_published": True,
        }.items():
            self.assertEqual(getattr(project, field), expected)
        for endpoint in ("v1:projects:list", "v1:portfolio:site"):
            self.assertIn("new-work", self.public_slugs(endpoint))

    def test_slug_is_generated_and_duplicate_slug_is_a_field_error(self):
        self.assertRedirects(self.client.post(self.create_url, self.payload(slug="")), self.list_url)
        response = self.client.post(self.create_url, self.payload(slug=""))
        self.assertEqual(response.status_code, 200)
        self.assertIn("slug", response.context["form"].errors)
        self.assertEqual(Project.objects.count(), 2)

    def test_non_ascii_title_requires_explicit_slug_when_not_derivable(self):
        response = self.client.post(self.create_url, self.payload(title="作品", slug=""))
        self.assertIn("slug", response.context["form"].errors)

    def test_required_fields_and_lengths_are_validated(self):
        response = self.client.post(self.create_url, self.payload(title="", category="", year="", summary="", description=""))
        for field in ("title", "category", "year", "summary", "description"):
            self.assertIn(field, response.context["form"].errors)
        response = self.client.post(self.create_url, self.payload(title="x" * 161, summary="x" * 301))
        self.assertIn("title", response.context["form"].errors)
        self.assertIn("summary", response.context["form"].errors)
        self.assertEqual(Project.objects.count(), 1)

    def test_invalid_urls_numbers_and_choices_show_errors_without_saving(self):
        response = self.client.post(self.create_url, self.payload(
            image_url="javascript:alert(1)", live_url="not a URL", source_url="ftp://example.com/source",
            year="0", sort_order="-1", accent="invalid",
        ))
        for field in ("image_url", "live_url", "source_url", "year", "sort_order", "accent"):
            self.assertIn(field, response.context["form"].errors)
        self.assertContains(response, "Please fix the highlighted fields")
        self.assertContains(response, 'aria-invalid="true"')
        self.assertContains(response, 'id="id_year_error"', count=1)
        self.assertEqual(Project.objects.count(), 1)

    def test_technology_validation_and_friendly_round_trip(self):
        for value in ("x" * 81, "\n".join(str(i) for i in range(31))):
            response = self.client.post(self.create_url, self.payload(technologies=value))
            self.assertIn("technologies", response.context["form"].errors)
        self.client.post(self.create_url, self.payload(technologies=" Django \n\nReact\nDjango"))
        project = Project.objects.get(slug="new-work")
        self.assertEqual(project.technologies, ["Django", "React"])
        response = self.client.get(reverse("dashboard:project-update", args=[project.pk]))
        self.assertEqual(response.context["form"]["technologies"].value(), "Django\nReact")

    def test_drafts_are_not_exposed_by_either_public_endpoint(self):
        self.client.post(self.create_url, self.payload(is_published=""))
        for endpoint in ("v1:projects:list", "v1:portfolio:site"):
            self.assertNotIn("new-work", self.public_slugs(endpoint))
        self.assertContains(self.client.get(self.list_url), "New work")

    def test_edit_prepopulates_data_and_retains_image_when_unchanged(self):
        response = self.client.get(self.edit_url)
        self.assertEqual(response.context["form"]["title"].value(), "Existing project")
        self.assertEqual(response.context["form"]["image_url"].value(), self.project.image_url)
        previous_update = self.project.updated_at
        response = self.client.post(self.edit_url, self.payload(slug="existing", image_url=self.project.image_url), follow=True)
        self.assertContains(response, 'Project &quot;New work&quot; updated.')
        self.project.refresh_from_db()
        self.assertEqual(self.project.image_url, "https://example.com/original.png")
        self.assertGreater(self.project.updated_at, previous_update)
        public = self.client.get(reverse("v1:portfolio:site")).json()["projects"][0]
        self.assertEqual(public["title"], "New work")
        self.assertEqual(public["image_url"], self.project.image_url)

    def test_image_url_can_be_replaced_and_explicitly_cleared(self):
        for value in ("https://example.com/replacement.webp", ""):
            self.assertRedirects(self.client.post(self.edit_url, self.payload(slug="existing", image_url=value)), self.list_url)
            self.project.refresh_from_db()
            self.assertEqual(self.project.image_url, value)

    def test_invalid_edit_preserves_database_and_entered_values(self):
        response = self.client.post(self.edit_url, self.payload(year="bad", title="Unsaved title"))
        self.assertEqual(response.context["form"]["title"].value(), "Unsaved title")
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Existing project")
        self.assertEqual(self.project.image_url, "https://example.com/original.png")

    def test_get_delete_only_confirms_and_post_removes_from_public_data(self):
        response = self.client.get(self.delete_url)
        self.assertContains(response, "Existing project")
        self.assertContains(response, "Are you sure")
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(self.client.delete(self.delete_url).status_code, 405)
        response = self.client.post(self.delete_url, follow=True)
        self.assertContains(response, 'Project &quot;Existing project&quot; deleted.')
        self.assertEqual(Project.objects.count(), 0)
        for endpoint in ("v1:projects:list", "v1:portfolio:site"):
            self.assertNotIn("existing", self.public_slugs(endpoint))

    def test_csrf_required_for_create_edit_and_delete(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for url in (self.create_url, self.edit_url, self.delete_url):
            self.assertEqual(client.post(url, self.payload()).status_code, 403)
        client.get(self.create_url)
        self.assertEqual(client.post(self.create_url, self.payload(), HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value).status_code, 302)
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

    def test_missing_objects_return_404(self):
        for route in ("project-update", "project-delete"):
            url = reverse(f"dashboard:{route}", args=[999999])
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url, self.payload()).status_code, 404)

    def test_search_filter_pagination_and_display_order(self):
        for number in range(12):
            Project.objects.create(title=f"Web {number}", slug=f"web-{number}", category="Backend", year=2026, sort_order=12-number)
        response = self.client.get(self.list_url)
        self.assertEqual(response.context["paginator"].count, 13)
        self.assertEqual(len(response.context["projects"]), 10)
        self.assertEqual(response.context["projects"][0].pk, self.project.pk)
        response = self.client.get(self.list_url, {"q": "Backend", "status": "draft", "page": 2})
        self.assertEqual(response.context["paginator"].count, 12)
        self.assertEqual(len(response.context["projects"]), 2)
        self.assertContains(response, "q=Backend&amp;status=draft")
        self.assertEqual(self.client.get(self.list_url, {"status": "published"}).context["paginator"].count, 1)

    def test_empty_and_filtered_empty_states(self):
        self.assertContains(self.client.get(self.list_url, {"q": "Missing"}), "No matching projects")
        Project.objects.all().delete()
        response = self.client.get(self.list_url)
        self.assertContains(response, "No projects yet")
        self.assertContains(response, f'href="{self.create_url}"')

    def test_project_content_is_escaped_and_only_published_has_public_link(self):
        Project.objects.filter(pk=self.project.pk).update(title="<script>bad()</script>", is_published=False)
        response = self.client.get(self.list_url)
        self.assertContains(response, "&lt;script&gt;bad()&lt;/script&gt;")
        self.assertNotContains(response, "#projects/existing")

    def test_overview_project_links_use_custom_dashboard(self):
        response = self.client.get(reverse("dashboard:home"))
        for url in (self.list_url, self.create_url, self.edit_url):
            self.assertContains(response, f'href="{url}"')
        self.assertNotContains(response, '/admin/projects/project/')
