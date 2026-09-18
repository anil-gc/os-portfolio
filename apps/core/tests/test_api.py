from types import SimpleNamespace

from django.urls import resolve, reverse
from rest_framework.response import Response
from rest_framework.reverse import reverse as api_reverse
from rest_framework.test import APIRequestFactory, APISimpleTestCase
from rest_framework.views import APIView


class HealthTests(APISimpleTestCase):
    def test_health_is_public_versioned_json_without_database_access(self):
        url = reverse("v1:core:health")
        self.assertEqual(url, "/api/v1/core/health/")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "version": "v1"})
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("no-store", response["Cache-Control"])

    def test_health_supports_head(self):
        response = self.client.head(reverse("v1:core:health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    def test_health_rejects_writes(self):
        for method in ("post", "put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(reverse("v1:core:health"))
                self.assertEqual(response.status_code, 405)

    def test_unmounted_versions_are_not_available(self):
        for url in ("/api/core/health/", "/api/v2/core/health/"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_drf_reverse_preserves_version_and_app_namespace(self):
        url = reverse("v1:core:health")
        match = resolve(url)
        raw_request = APIRequestFactory().get(url)
        raw_request.resolver_match = match
        view = match.func.view_class()
        request = view.initialize_request(raw_request)
        view.initial(request)
        self.assertEqual(request.version, "v1")
        self.assertEqual(
            api_reverse("core:health", request=request), f"http://testserver{url}"
        )


class DefaultPermissionTests(APISimpleTestCase):
    def test_views_require_staff_unless_they_explicitly_override_permissions(self):
        class ProtectedView(APIView):
            def get(self, request):
                return Response({"ok": True})

        view = ProtectedView.as_view()
        request = APIRequestFactory().get("/")
        self.assertEqual(view(request).status_code, 403)

        for is_staff in (False, True):
            with self.subTest(is_staff=is_staff):
                request = APIRequestFactory().get("/")
                request.user = SimpleNamespace(is_active=True, is_staff=is_staff)
                self.assertEqual(view(request).status_code, 200 if is_staff else 403)
