from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from apps.dashboard.throttling import (
    LOGIN_FAILURE_LIMIT,
    LOGIN_FAILURE_WINDOW,
    login_cache_key,
)


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "dashboard-tests"}},
    DASHBOARD_TRUST_PROXY_IP=False,
)
class DashboardAccessTests(TestCase):
    password = "test-only-password"

    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.staff = users.objects.create_user("editor", password=cls.password, is_staff=True)
        cls.visitor = users.objects.create_user("visitor", password=cls.password)
        cls.inactive = users.objects.create_user("inactive", password=cls.password, is_staff=True, is_active=False)
        cls.superuser = users.objects.create_superuser("owner", password=cls.password)

    def setUp(self):
        cache.clear()
        self.home = reverse("dashboard:home")
        self.login = reverse("dashboard:login")
        self.logout = reverse("dashboard:logout")

    def sign_in(self, **extra):
        return self.client.post(self.login, {"username": "editor", "password": self.password, **extra})

    def assert_private(self, response):
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertIn("private", response.headers["Cache-Control"])

    def test_anonymous_dashboard_redirects_without_rendering_private_page(self):
        response = self.client.get(self.home)
        self.assertRedirects(response, self.login + "?next=" + self.home)
        self.assert_private(response)

    def test_staff_can_open_workspace_without_content_permissions(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.home)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to your workspace.")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assert_private(response)

    def test_superuser_can_open_workspace(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(self.home).status_code, 200)

    def test_nonstaff_cannot_open_workspace_even_with_model_permissions(self):
        self.visitor.user_permissions.add(Permission.objects.get(codename="change_project"))
        self.client.force_login(self.visitor)
        response = self.client.get(self.home)
        self.assertContains(response, "Access restricted.", status_code=403)
        self.assert_private(response)

    def test_revoked_staff_access_is_checked_on_every_request(self):
        self.client.force_login(self.staff)
        get_user_model().objects.filter(pk=self.staff.pk).update(is_staff=False)
        self.assertEqual(self.client.get(self.home).status_code, 403)

    def test_deactivated_session_no_longer_opens_workspace(self):
        self.client.force_login(self.staff)
        get_user_model().objects.filter(pk=self.staff.pk).update(is_active=False)
        self.assertEqual(self.client.get(self.home).status_code, 302)

    def test_valid_login_uses_existing_session_authentication(self):
        response = self.sign_in()
        self.assertRedirects(response, self.home, fetch_redirect_response=False)
        self.assertEqual(int(self.client.session[SESSION_KEY]), self.staff.pk)
        self.assert_private(response)
        self.assertContains(self.client.get(self.home), "signed in")

    def test_invalid_nonstaff_and_inactive_credentials_have_same_error(self):
        errors = []
        for username in ("missing", "visitor", "inactive"):
            response = self.client.post(self.login, {"username": username, "password": self.password})
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(SESSION_KEY, self.client.session)
            errors.append(list(response.context["form"].non_field_errors()))
        self.assertTrue(errors[0])
        self.assertEqual(errors[0], errors[1])
        self.assertEqual(errors[1], errors[2])

    def test_blank_login_is_validated_without_signing_in(self):
        response = self.client.post(self.login, {})
        self.assertEqual(response.status_code, 200)
        self.assertIn("username", response.context["form"].errors)
        self.assertIn("password", response.context["form"].errors)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_external_login_redirects_are_rejected(self):
        for destination in ("https://evil.example/", "//evil.example/", "///evil.example/"):
            with self.subTest(destination=destination):
                self.client.logout()
                self.assertRedirects(self.sign_in(next=destination), self.home)

    def test_local_login_destination_is_preserved(self):
        self.assertRedirects(self.sign_in(next=self.home + "?from=login"), self.home + "?from=login")

    def test_signed_in_staff_login_page_returns_to_workspace(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.login, {"next": "https://evil.example/"})
        self.assertRedirects(response, self.home)
        self.assert_private(response)

    def test_signed_in_nonstaff_can_still_see_login_form(self):
        self.client.force_login(self.visitor)
        self.assertContains(self.client.get(self.login), 'name="password"')

    def test_login_destination_cannot_loop_back_to_login(self):
        self.client.force_login(self.staff)
        self.assertRedirects(self.client.get(self.login, {"next": self.login}), self.home)

    def test_logout_requires_post_and_clears_session(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.logout).status_code, 405)
        self.assertIn(SESSION_KEY, self.client.session)
        response = self.client.post(self.logout)
        self.assertRedirects(response, self.login, fetch_redirect_response=False)
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assert_private(response)
        self.assertContains(self.client.get(self.login), "signed out")

    def test_logout_rejects_external_redirect(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.logout, {"next": "https://evil.example/"})
        self.assertRedirects(response, self.login)

    def test_login_and_logout_enforce_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.get(self.login)
        credentials = {"username": "editor", "password": self.password}
        self.assertEqual(client.post(self.login, credentials).status_code, 403)
        token = client.cookies["csrftoken"].value
        self.assertEqual(client.post(self.login, credentials, HTTP_X_CSRFTOKEN=token).status_code, 302)
        self.assertEqual(client.post(self.logout).status_code, 403)
        self.assertIn(SESSION_KEY, client.session)
        token = client.cookies["csrftoken"].value
        self.assertEqual(client.post(self.logout, HTTP_X_CSRFTOKEN=token).status_code, 302)
        self.assertNotIn(SESSION_KEY, client.session)

    def test_login_failures_are_throttled_per_address(self):
        for _ in range(LOGIN_FAILURE_LIMIT):
            self.client.post(self.login, {"username": "editor", "password": "wrong"})
        response = self.sign_in()
        self.assertContains(response, "Too many sign-in attempts", status_code=429)
        self.assertEqual(response.headers["Retry-After"], str(LOGIN_FAILURE_WINDOW))
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assert_private(response)
        other = Client(REMOTE_ADDR="192.0.2.20")
        self.assertEqual(other.post(self.login, {"username": "editor", "password": self.password}).status_code, 302)
        # Expiring the cache window permits a new attempt.
        cache.clear()
        self.assertEqual(self.sign_in().status_code, 302)

    def test_client_cannot_bypass_limit_with_untrusted_headers(self):
        factory = RequestFactory()
        first = factory.post(self.login, REMOTE_ADDR="192.0.2.1", HTTP_X_REAL_IP="192.0.2.2")
        second = factory.post(self.login, REMOTE_ADDR="192.0.2.1", HTTP_X_REAL_IP="192.0.2.3")
        self.assertEqual(login_cache_key(first), login_cache_key(second))
        self.assertNotIn("192.0.2.1", login_cache_key(first))

    @override_settings(DASHBOARD_TRUST_PROXY_IP=True)
    def test_trusted_proxy_uses_valid_overwritten_address_only(self):
        factory = RequestFactory()
        first = factory.post(self.login, REMOTE_ADDR="192.0.2.1", HTTP_X_REAL_IP="192.0.2.2")
        second = factory.post(self.login, REMOTE_ADDR="192.0.2.1", HTTP_X_REAL_IP="192.0.2.3")
        invalid = factory.post(self.login, REMOTE_ADDR="192.0.2.1", HTTP_X_REAL_IP="spoofed,chain")
        peer = factory.post(self.login, REMOTE_ADDR="192.0.2.1")
        self.assertNotEqual(login_cache_key(first), login_cache_key(second))
        self.assertEqual(login_cache_key(invalid), login_cache_key(peer))

    @override_settings(ROOT_URLCONF="apps.dashboard.tests.urls")
    def test_reusable_gate_enforces_model_permissions(self):
        self.assertEqual(self.client.get("/permission-probe/").status_code, 302)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get("/permission-probe/").status_code, 403)
        self.staff.user_permissions.add(Permission.objects.get(codename="change_project"))
        self.assertEqual(self.client.get("/permission-probe/").status_code, 200)

    @override_settings(DASHBOARD_PUBLIC_SITE_URL="https://portfolio.example/")
    def test_public_link_uses_configured_origin(self):
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(self.home), 'href="https://portfolio.example/"')

    def test_admin_and_public_health_routes_remain_available(self):
        self.assertEqual(self.client.get(reverse("admin:login")).status_code, 200)
        self.assertEqual(self.client.get(reverse("v1:core:health")).status_code, 200)
