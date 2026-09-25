from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.certificates.models import Certificate
from apps.education.models import Education
from apps.experience.models import Experience
from apps.portfolio.models import Profile


class EntryManagementTests:
    """Run the same permission and persistence contracts for each concrete module."""

    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.owner = users.objects.create_superuser("entry-owner")
        cls.staff = users.objects.create_user("entry-staff", is_staff=True)
        cls.visitor = users.objects.create_user("entry-visitor")
        cls.inactive = users.objects.create_user("entry-inactive", is_staff=True, is_active=False)
        values = {**cls.valid_data, cls.title_field: "Existing entry", "sort_order": 0, "is_published": True}
        cls.entry = cls.model.objects.create(**values)
        Profile.objects.create(name="Owner")

    def setUp(self):
        self.client.force_login(self.owner)
        self.list_url = reverse(f"dashboard:{self.route}-list")
        self.create_url = reverse(f"dashboard:{self.route}-create")
        self.edit_url = reverse(f"dashboard:{self.route}-update", args=[self.entry.pk])
        self.delete_url = reverse(f"dashboard:{self.route}-delete", args=[self.entry.pk])

    def payload(self, **overrides):
        return {**self.valid_data, "sort_order": "2", "is_published": "on", **overrides}

    def grant(self, *actions):
        opts = self.model._meta
        self.staff.user_permissions.set(Permission.objects.filter(
            content_type__app_label=opts.app_label,
            codename__in=[f"{action}_{opts.model_name}" for action in actions],
        ))
        self.client.force_login(self.staff)

    def public_entries(self):
        for endpoint in (f"v1:{self.section}:list", "v1:portfolio:site"):
            response = Client().get(reverse(endpoint))
            self.assertEqual(response.status_code, 200)
            data = response.json()
            yield data[self.section] if isinstance(data, dict) else data

    def test_anonymous_cannot_get_or_post_any_management_route(self):
        self.client.logout()
        for url in (self.list_url, self.create_url, self.edit_url, self.delete_url):
            for method in (self.client.get, self.client.post):
                with self.subTest(url=url, method=method.__name__):
                    response = method(url, self.payload())
                    self.assertEqual(response.status_code, 302)
                    self.assertTrue(response.url.startswith(reverse("dashboard:login")))
        self.assertEqual(self.model.objects.count(), 1)

    def test_permissionless_staff_and_nonstaff_cannot_access_or_modify(self):
        self.visitor.user_permissions.set(Permission.objects.filter(content_type__app_label=self.model._meta.app_label))
        for user in (self.staff, self.visitor):
            self.client.force_login(user)
            for url in (self.list_url, self.create_url, self.edit_url, self.delete_url):
                for method in (self.client.get, self.client.post):
                    with self.subTest(user=user.username, url=url, method=method.__name__):
                        self.assertEqual(method(url, self.payload()).status_code, 403)
        self.assertEqual(getattr(self.model.objects.get(), self.title_field), "Existing entry")

    def test_inactive_staff_cannot_access_or_modify(self):
        self.client.force_login(self.inactive)
        for url in (self.list_url, self.create_url, self.edit_url, self.delete_url):
            self.assertEqual(self.client.get(url).status_code, 302)
            self.assertEqual(self.client.post(url, self.payload()).status_code, 302)
        self.assertTrue(self.model.objects.filter(pk=self.entry.pk).exists())

    def test_owner_can_access_all_pages_with_private_responses(self):
        for url in (self.list_url, self.create_url, self.edit_url, self.delete_url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIn("no-store", response.headers["Cache-Control"])
            self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_view_only_staff_cannot_mutate_and_actions_are_hidden(self):
        self.grant("view")
        response = self.client.get(self.list_url)
        self.assertContains(response, "Existing entry")
        for url in (self.create_url, self.edit_url, self.delete_url):
            self.assertNotContains(response, f'href="{url}"')
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, self.payload()).status_code, 403)

    def test_add_only_staff_can_create_and_return_to_accessible_home(self):
        self.grant("add")
        self.assertEqual(self.client.get(self.create_url).status_code, 200)
        self.assertRedirects(self.client.post(self.create_url, self.payload()), reverse("dashboard:home"))
        for url in (self.list_url, self.edit_url, self.delete_url):
            self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.model.objects.count(), 2)

    def test_change_only_staff_can_list_and_edit_but_not_add_or_delete(self):
        self.grant("change")
        self.assertEqual(self.client.get(self.list_url).status_code, 200)
        self.assertRedirects(self.client.post(self.edit_url, self.payload()), self.list_url)
        for url in (self.create_url, self.delete_url):
            self.assertEqual(self.client.post(url, self.payload()).status_code, 403)

    def test_delete_only_staff_can_confirm_and_delete_then_return_home(self):
        self.grant("delete")
        self.assertEqual(self.client.get(self.delete_url).status_code, 200)
        self.assertEqual(self.client.get(self.list_url).status_code, 403)
        for url in (self.create_url, self.edit_url):
            self.assertEqual(self.client.post(url, self.payload()).status_code, 403)
        self.assertRedirects(self.client.post(self.delete_url), reverse("dashboard:home"))
        self.assertEqual(self.model.objects.count(), 0)

    def test_valid_create_saves_all_fields_and_reaches_public_apis(self):
        response = self.client.post(self.create_url, self.payload(), follow=True)
        self.assertContains(response, "created.")
        entry = self.model.objects.exclude(pk=self.entry.pk).get()
        for field, expected in self.valid_data.items():
            self.assertEqual(str(getattr(entry, field)), str(expected))
        self.assertTrue(entry.is_published)
        self.assertEqual(entry.sort_order, 2)
        for data in self.public_entries():
            public = next(item for item in data if item["id"] == entry.pk)
            for field, expected in self.valid_data.items():
                self.assertEqual(public[field], expected)

    def test_required_fields_and_order_are_validated_without_saving(self):
        for field in self.required_fields:
            response = self.client.post(self.create_url, self.payload(**{field: ""}))
            self.assertEqual(response.status_code, 200)
            self.assertIn(field, response.context["form"].errors)
        for value in ("", "abc", "-1", "1.5", "2147483648"):
            response = self.client.post(self.create_url, self.payload(sort_order=value))
            self.assertIn("sort_order", response.context["form"].errors)
        for field in (self.title_field, self.subtitle_field):
            response = self.client.post(self.create_url, self.payload(**{field: "x" * 161}))
            self.assertIn(field, response.context["form"].errors)
        self.assertEqual(self.model.objects.count(), 1)

    def test_edit_prepopulates_dates_and_preserves_values(self):
        response = self.client.get(self.edit_url)
        self.assertEqual(response.context["form"].initial[self.title_field], "Existing entry")
        self.assertContains(response, 'type="date"')
        for field, value in self.valid_data.items():
            if "date" in field:
                self.assertContains(response, f'value="{value}"')
        response = self.client.post(self.edit_url, self.payload(**{self.title_field: "Updated entry"}), follow=True)
        self.assertContains(response, "updated.")
        self.entry.refresh_from_db()
        self.assertEqual(getattr(self.entry, self.title_field), "Updated entry")
        for field, value in self.valid_data.items():
            if field != self.title_field:
                self.assertEqual(str(getattr(self.entry, field)), str(value))
        for data in self.public_entries():
            self.assertEqual(data[0][self.title_field], "Updated entry")

    def test_invalid_edit_preserves_saved_record(self):
        response = self.client.post(self.edit_url, self.payload(**{self.title_field: ""}))
        self.assertIn(self.title_field, response.context["form"].errors)
        self.entry.refresh_from_db()
        self.assertEqual(getattr(self.entry, self.title_field), "Existing entry")

    def test_drafts_publish_and_unpublish_through_public_apis(self):
        self.client.post(self.edit_url, self.payload(is_published=""))
        for data in self.public_entries():
            self.assertEqual(data, [])
        self.client.post(self.edit_url, self.payload())
        for data in self.public_entries():
            self.assertEqual(data[0][self.title_field], self.valid_data[self.title_field])
        self.client.post(self.create_url, self.payload(is_published=""))
        for data in self.public_entries():
            self.assertEqual(len(data), 1)

    def test_get_confirms_and_post_deletes_from_both_public_apis(self):
        response = self.client.get(self.delete_url)
        self.assertContains(response, "Existing entry")
        self.assertContains(response, "Are you sure")
        self.assertTrue(self.model.objects.filter(pk=self.entry.pk).exists())
        self.assertEqual(self.client.delete(self.delete_url).status_code, 405)
        self.assertTrue(self.model.objects.filter(pk=self.entry.pk).exists())
        response = self.client.post(self.delete_url, follow=True)
        self.assertContains(response, "deleted.")
        self.assertEqual(self.model.objects.count(), 0)
        for data in self.public_entries():
            self.assertEqual(data, [])

    def test_csrf_required_for_all_mutations(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for url in (self.create_url, self.edit_url, self.delete_url):
            self.assertEqual(client.post(url, self.payload()).status_code, 403)
        client.get(self.create_url)
        self.assertEqual(client.post(self.create_url, self.payload(), HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value).status_code, 302)
        self.assertTrue(self.model.objects.filter(pk=self.entry.pk).exists())

    def test_missing_entries_return_404(self):
        for action in ("update", "delete"):
            url = reverse(f"dashboard:{self.route}-{action}", args=[999999])
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url, self.payload()).status_code, 404)

    def test_search_filters_pagination_and_bounded_queries(self):
        for number in range(12):
            self.model.objects.create(**{**self.valid_data, self.title_field: f"Item {number}", "sort_order": number+1})
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.list_url)
        self.assertEqual(response.context["paginator"].count, 13)
        self.assertEqual(len(response.context["entries"]), 10)
        self.assertEqual(response.context["entries"][0]["object"].pk, self.entry.pk)
        self.assertEqual(len(queries), 4)
        select = next(q["sql"] for q in queries if "LIMIT 10" in q["sql"])
        self.assertNotIn('"description"', select)
        response = self.client.get(self.list_url, {"q": "Item", "status": "draft", "page": 2})
        self.assertEqual(response.context["paginator"].count, 12)
        self.assertEqual(len(response.context["entries"]), 2)
        self.assertContains(response, "q=Item&amp;status=draft")
        self.assertEqual(self.client.get(self.list_url, {"status": "published"}).context["paginator"].count, 1)
        self.assertEqual(self.client.get(self.list_url, {"q": self.valid_data[self.subtitle_field]}).context["paginator"].count, 13)

    def test_display_order_reaches_both_public_apis(self):
        self.client.post(self.create_url, self.payload(sort_order="0"))
        self.client.post(self.edit_url, self.payload(sort_order="8", **{self.title_field: "Last entry"}))
        for data in self.public_entries():
            self.assertEqual([item[self.title_field] for item in data], [self.valid_data[self.title_field], "Last entry"])

    def test_empty_states_escaped_content_and_navigation(self):
        self.model.objects.filter(pk=self.entry.pk).update(**{self.title_field: "<script>bad()</script>"})
        response = self.client.get(self.list_url)
        self.assertContains(response, "&lt;script&gt;bad()&lt;/script&gt;")
        self.assertContains(response, f'href="{self.list_url}" aria-current="page"')
        self.assertContains(self.client.get(self.list_url, {"q": "Missing"}), "No matching entries")
        self.model.objects.all().delete()
        response = self.client.get(self.list_url)
        self.assertContains(response, f"No {self.section} entries yet")
        self.assertContains(response, f'href="{self.create_url}"')

    def test_other_module_permissions_do_not_grant_access(self):
        self.staff.user_permissions.set(Permission.objects.filter(content_type__app_label="projects"))
        self.client.force_login(self.staff)
        for url in (self.list_url, self.create_url, self.edit_url, self.delete_url):
            self.assertEqual(self.client.get(url).status_code, 403)


class DateRangeTests:
    def test_invalid_date_ranges_show_end_date_error_and_do_not_save(self):
        for url in (self.create_url, self.edit_url):
            response = self.client.post(url, self.payload(start_date="2025-06-01", end_date="2024-01-01"))
            self.assertIn("end_date", response.context["form"].errors)
            self.assertContains(response, "End date cannot precede the start date.")
        self.entry.refresh_from_db()
        self.assertEqual(str(self.entry.end_date), self.valid_data["end_date"])
        self.assertEqual(self.model.objects.count(), 1)

    def test_blank_end_date_is_present_and_can_be_replaced_or_cleared(self):
        for end_date in ("", "2025-06-01", ""):
            self.assertRedirects(self.client.post(self.edit_url, self.payload(end_date=end_date)), self.list_url)
            self.entry.refresh_from_db()
            self.assertEqual(str(self.entry.end_date) if self.entry.end_date else "", end_date)
            for data in self.public_entries():
                self.assertEqual(data[0]["end_date"], end_date or None)
        self.assertContains(self.client.get(self.list_url), "Present")

    def test_invalid_calendar_date_and_long_description_are_rejected(self):
        response = self.client.post(self.create_url, self.payload(start_date="2025-02-30", description="x"*8001))
        self.assertIn("start_date", response.context["form"].errors)
        self.assertIn("description", response.context["form"].errors)


class ExperienceManagementTests(EntryManagementTests, DateRangeTests, TestCase):
    model = Experience
    route = section = "experience"
    title_field, subtitle_field = "role", "company"
    required_fields = ("role", "company", "start_date", "description")
    valid_data = {"role": "Developer", "company": "Example team", "location": "Remote", "start_date": "2024-01-01", "end_date": "2025-06-01", "description": "Built useful software."}


class EducationManagementTests(EntryManagementTests, DateRangeTests, TestCase):
    model = Education
    route = section = "education"
    title_field, subtitle_field = "degree", "institution"
    required_fields = ("degree", "institution", "start_date")
    valid_data = {"degree": "Computing qualification", "institution": "Example institution", "location": "Kathmandu", "start_date": "2024-01-01", "end_date": "2025-06-01", "description": "Studied computing."}

    def test_optional_education_fields_can_be_blank(self):
        self.assertRedirects(self.client.post(self.create_url, self.payload(description="", location="", end_date="")), self.list_url)


class CertificateManagementTests(EntryManagementTests, TestCase):
    model = Certificate
    route = "certificate"
    section = "certificates"
    title_field, subtitle_field = "title", "issuer"
    required_fields = ("title", "issuer", "issued_date")
    valid_data = {"title": "Software certificate", "issuer": "Example issuer", "issued_date": "2025-06-01", "credential_url": "https://example.com/verify", "description": "Completed a course."}

    def test_invalid_credential_urls_dates_and_description_are_rejected(self):
        for value in ("not-a-url", "javascript:alert(1)", "ftp://example.com/file"):
            response = self.client.post(self.create_url, self.payload(credential_url=value))
            self.assertIn("credential_url", response.context["form"].errors)
            self.assertEqual(len(response.context["form"].errors["credential_url"]), 1)
        response = self.client.post(self.create_url, self.payload(issued_date="2025-02-30", description="x"*4001))
        self.assertIn("issued_date", response.context["form"].errors)
        self.assertIn("description", response.context["form"].errors)
        self.assertEqual(Certificate.objects.count(), 1)

    def test_credential_url_is_preserved_replaced_and_cleared(self):
        for url in (self.valid_data["credential_url"], "https://example.com/replaced", ""):
            self.client.post(self.edit_url, self.payload(credential_url=url))
            self.entry.refresh_from_db()
            self.assertEqual(self.entry.credential_url, url)
            for data in self.public_entries():
                self.assertEqual(data[0]["credential_url"], url)
        self.assertRedirects(self.client.post(self.create_url, self.payload(credential_url="", description="")), self.list_url)

    def test_overview_uses_custom_certificate_and_experience_links(self):
        response = self.client.get(reverse("dashboard:home"))
        for route in ("certificate-list", "certificate-create", "experience-list"):
            self.assertContains(response, f'href="{reverse(f"dashboard:{route}")}"')
        self.assertNotContains(response, "/admin/certificates/certificate/")
        self.assertNotContains(response, "/admin/experience/experience/")
