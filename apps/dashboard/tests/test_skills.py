from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.portfolio.models import Profile
from apps.skills.models import Skill


class SkillManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.owner = users.objects.create_superuser("skill-owner")
        cls.staff = users.objects.create_user("skill-staff", is_staff=True)
        cls.visitor = users.objects.create_user("skill-visitor")
        cls.inactive = users.objects.create_user("skill-inactive", is_staff=True, is_active=False)
        cls.skill = Skill.objects.create(name="Python", category="Backend", level="Advanced", is_published=True)
        Profile.objects.create(name="Owner")

    def setUp(self):
        self.client.force_login(self.owner)
        self.list_url = reverse("dashboard:skill-list")
        self.create_url = reverse("dashboard:skill-create")
        self.edit_url = reverse("dashboard:skill-update", args=[self.skill.pk])
        self.delete_url = reverse("dashboard:skill-delete", args=[self.skill.pk])

    def payload(self, **overrides):
        return {"name": "Django", "category": "Backend", "level": "Proficient", "sort_order": "2", "is_published": "on", **overrides}

    def grant(self, *permissions):
        self.staff.user_permissions.set(Permission.objects.filter(content_type__app_label="skills", codename__in=permissions))
        self.client.force_login(self.staff)

    def public_skills(self):
        # Check both public routes as an unauthenticated visitor.
        client = Client()
        for endpoint in ("v1:skills:list", "v1:portfolio:site"):
            response = client.get(reverse(endpoint))
            self.assertEqual(response.status_code, 200)
            data = response.json()
            yield data["skills"] if isinstance(data, dict) else data

    def test_anonymous_cannot_get_or_post_any_route(self):
        self.client.logout()
        for url in (self.list_url, self.create_url, self.edit_url, self.delete_url):
            for method in (self.client.get, self.client.post):
                with self.subTest(url=url, method=method.__name__):
                    response = method(url, self.payload())
                    self.assertEqual(response.status_code, 302)
                    self.assertTrue(response.url.startswith(reverse("dashboard:login")))
        self.assertEqual(Skill.objects.count(), 1)

    def test_nonstaff_and_permissionless_staff_cannot_read_or_mutate(self):
        self.visitor.user_permissions.set(Permission.objects.filter(content_type__app_label="skills"))
        for user in (self.visitor, self.staff):
            self.client.force_login(user)
            for url in (self.list_url, self.create_url, self.edit_url, self.delete_url):
                for method in (self.client.get, self.client.post):
                    with self.subTest(user=user.username, url=url, method=method.__name__):
                        self.assertEqual(method(url, self.payload()).status_code, 403)
        self.assertEqual(Skill.objects.get().name, "Python")

    def test_inactive_staff_cannot_access_or_delete(self):
        self.client.force_login(self.inactive)
        for url in (self.list_url, self.create_url, self.edit_url, self.delete_url):
            self.assertEqual(self.client.get(url).status_code, 302)
            self.assertEqual(self.client.post(url, self.payload()).status_code, 302)
        self.assertTrue(Skill.objects.filter(pk=self.skill.pk).exists())

    def test_owner_can_open_all_pages_and_responses_are_private(self):
        for url in (self.list_url, self.create_url, self.edit_url, self.delete_url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIn("no-store", response.headers["Cache-Control"])
            self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_view_permission_cannot_mutate_and_actions_are_hidden(self):
        self.grant("view_skill")
        response = self.client.get(self.list_url)
        self.assertContains(response, "Python")
        for url in (self.create_url, self.edit_url, self.delete_url):
            self.assertNotContains(response, f'href="{url}"')
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, self.payload()).status_code, 403)

    def test_add_only_staff_can_create_and_return_home(self):
        self.grant("add_skill")
        self.assertEqual(self.client.get(self.create_url).status_code, 200)
        self.assertRedirects(self.client.post(self.create_url, self.payload()), reverse("dashboard:home"))
        for url in (self.list_url, self.edit_url, self.delete_url):
            self.assertEqual(self.client.get(url).status_code, 403)
        self.assertTrue(Skill.objects.filter(name="Django").exists())

    def test_change_only_staff_can_list_and_edit_but_not_add_or_delete(self):
        self.grant("change_skill")
        self.assertEqual(self.client.get(self.list_url).status_code, 200)
        self.assertRedirects(self.client.post(self.edit_url, self.payload()), self.list_url)
        for url in (self.create_url, self.delete_url):
            self.assertEqual(self.client.post(url, self.payload()).status_code, 403)

    def test_delete_only_staff_can_confirm_and_delete_then_return_home(self):
        self.grant("delete_skill")
        self.assertEqual(self.client.get(self.delete_url).status_code, 200)
        self.assertEqual(self.client.get(self.list_url).status_code, 403)
        for url in (self.create_url, self.edit_url):
            self.assertEqual(self.client.post(url, self.payload()).status_code, 403)
        self.assertRedirects(self.client.post(self.delete_url), reverse("dashboard:home"))
        self.assertEqual(Skill.objects.count(), 0)

    def test_create_saves_all_fields_and_reaches_both_public_apis(self):
        response = self.client.post(self.create_url, self.payload(), follow=True)
        self.assertContains(response, 'Skill &quot;Django&quot; created.')
        skill = Skill.objects.get(name="Django")
        self.assertEqual((skill.category, skill.level, skill.sort_order, skill.is_published), ("Backend", "Proficient", 2, True))
        for data in self.public_skills():
            self.assertIn({"id": skill.pk, "name": "Django", "category": "Backend", "level": "Proficient"}, data)

    def test_server_validation_rejects_invalid_fields_without_saving(self):
        invalid_values = {
            "name": ("", "   ", "a" * 101), "category": ("", "   ", "a" * 81),
            "level": ("", "Expert", "95%"), "sort_order": ("", "abc", "-1", "1.5", "2147483648"),
        }
        for field, values in invalid_values.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    response = self.client.post(self.create_url, self.payload(**{field: value}))
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(field, response.context["form"].errors)
                    self.assertContains(response, "Please fix the highlighted fields.")
        self.assertEqual(Skill.objects.count(), 1)

    def test_duplicate_name_errors_on_create_and_edit(self):
        Skill.objects.create(name="Django", category="Backend")
        for url in (self.create_url, self.edit_url):
            response = self.client.post(url, self.payload())
            self.assertIn("name", response.context["form"].errors)
        self.skill.refresh_from_db()
        self.assertEqual(self.skill.name, "Python")

    def test_form_prepopulates_existing_values_and_distinct_category_suggestions(self):
        Skill.objects.create(name="Django", category="Backend")
        response = self.client.get(self.edit_url)
        form = response.context["form"]
        self.assertEqual(form.initial["name"], "Python")
        self.assertEqual(form.initial["level"], "Advanced")
        self.assertEqual(form.initial["sort_order"], 0)
        self.assertTrue(form.initial["is_published"])
        self.assertEqual(list(form.categories), ["Backend"])

    def test_update_preserves_values_and_public_data_then_moves_category_and_order(self):
        response = self.client.post(self.edit_url, self.payload(name="Python", level="Advanced", sort_order="0"), follow=True)
        self.assertContains(response, 'Skill &quot;Python&quot; updated.')
        self.skill.refresh_from_db()
        self.assertEqual((self.skill.category, self.skill.level, self.skill.sort_order, self.skill.is_published), ("Backend", "Advanced", 0, True))
        self.client.post(self.edit_url, self.payload(name="Python 3", category="Languages", level="Learning", sort_order="5"))
        for data in self.public_skills():
            self.assertEqual(data, [{"id": self.skill.pk, "name": "Python 3", "category": "Languages", "level": "Learning"}])
        self.skill.refresh_from_db()
        self.assertEqual(self.skill.sort_order, 5)

    def test_invalid_edit_preserves_saved_record(self):
        self.client.post(self.edit_url, self.payload(name="", level="Unknown"))
        self.skill.refresh_from_db()
        self.assertEqual((self.skill.name, self.skill.level, self.skill.sort_order), ("Python", "Advanced", 0))

    def test_drafts_are_hidden_and_publishing_and_unpublishing_reach_public_apis(self):
        self.client.post(self.create_url, self.payload(is_published=""))
        draft = Skill.objects.get(name="Django")
        edit_url = reverse("dashboard:skill-update", args=[draft.pk])
        for data in self.public_skills():
            self.assertNotIn("Django", [item["name"] for item in data])
        self.client.post(edit_url, self.payload())
        for data in self.public_skills():
            self.assertIn("Django", [item["name"] for item in data])
        self.client.post(edit_url, self.payload(is_published=""))
        for data in self.public_skills():
            self.assertNotIn("Django", [item["name"] for item in data])

    def test_get_delete_only_confirms_and_post_removes_public_record(self):
        response = self.client.get(self.delete_url)
        self.assertContains(response, "Python")
        self.assertContains(response, "Are you sure")
        self.assertTrue(Skill.objects.filter(pk=self.skill.pk).exists())
        self.assertEqual(self.client.delete(self.delete_url).status_code, 405)
        response = self.client.post(self.delete_url, follow=True)
        self.assertContains(response, 'Skill &quot;Python&quot; deleted.')
        self.assertEqual(Skill.objects.count(), 0)
        for data in self.public_skills():
            self.assertEqual(data, [])

    def test_csrf_required_for_all_mutations(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for url in (self.create_url, self.edit_url, self.delete_url):
            self.assertEqual(client.post(url, self.payload()).status_code, 403)
        client.get(self.create_url)
        self.assertEqual(client.post(self.create_url, self.payload(), HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value).status_code, 302)
        self.assertTrue(Skill.objects.filter(pk=self.skill.pk).exists())

    def test_missing_objects_return_404(self):
        for route in ("skill-update", "skill-delete"):
            url = reverse(f"dashboard:{route}", args=[999999])
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url, self.payload()).status_code, 404)

    def test_search_filter_pagination_and_ordering(self):
        for number in range(22):
            Skill.objects.create(name=f"Tool {number}", category="Tools", sort_order=22-number)
        response = self.client.get(self.list_url)
        self.assertEqual(response.context["paginator"].count, 23)
        self.assertEqual(len(response.context["skills"]), 20)
        self.assertEqual(response.context["skills"][0].pk, self.skill.pk)
        response = self.client.get(self.list_url, {"q": "Tools", "status": "draft", "page": 2})
        self.assertEqual(response.context["paginator"].count, 22)
        self.assertEqual(len(response.context["skills"]), 2)
        self.assertContains(response, "q=Tools&amp;status=draft")
        self.assertEqual(self.client.get(self.list_url, {"status": "published"}).context["paginator"].count, 1)

    def test_public_order_uses_sort_order_then_id(self):
        self.client.post(self.create_url, self.payload(sort_order="0"))
        self.client.post(self.edit_url, self.payload(name="Python", sort_order="3"))
        self.client.post(self.create_url, self.payload(name="Flask", sort_order="0"))
        for data in self.public_skills():
            self.assertEqual([item["name"] for item in data], ["Django", "Flask", "Python"])

    def test_empty_states_and_escaped_content(self):
        Skill.objects.filter(pk=self.skill.pk).update(name="<script>bad()</script>")
        self.assertContains(self.client.get(self.list_url), "&lt;script&gt;bad()&lt;/script&gt;")
        self.assertContains(self.client.get(self.list_url, {"q": "Missing"}), "No matching skills")
        Skill.objects.all().delete()
        response = self.client.get(self.list_url)
        self.assertContains(response, "No skills added yet")
        self.assertContains(response, f'href="{self.create_url}"')

    def test_overview_and_sidebar_use_custom_skill_routes(self):
        response = self.client.get(reverse("dashboard:home"))
        for url in (self.list_url, self.create_url):
            self.assertContains(response, f'href="{url}"')
        self.assertNotContains(response, "/admin/skills/skill/")
        self.assertContains(self.client.get(self.list_url), f'href="{self.list_url}" aria-current="page"')

    def test_list_queries_stay_bounded_with_many_skills(self):
        Skill.objects.bulk_create([Skill(name=f"Tool {i}", category="Tools") for i in range(35)])
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        # Session, user, pagination count, and one limited skill query.
        self.assertEqual(len(queries), 4)
        self.assertTrue(any("LIMIT 20" in query["sql"] for query in queries))
