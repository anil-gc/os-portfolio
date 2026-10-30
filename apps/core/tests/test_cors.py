from django.test import Client, SimpleTestCase, override_settings


FRONTEND = "https://os-portfolio-o54c.vercel.app"


@override_settings(CORS_ALLOWED_ORIGINS=[FRONTEND])
class FrontendCorsTests(SimpleTestCase):
    def test_allowed_frontend_can_read_api_without_cookie_access(self):
        response = self.client.get("/api/v1/core/health/", HTTP_ORIGIN=FRONTEND)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], FRONTEND)
        self.assertIn("origin", response["Vary"].lower())
        self.assertNotIn("Access-Control-Allow-Credentials", response)

    def test_other_origins_cannot_read_api(self):
        for origin in ("https://untrusted.example", FRONTEND + ".evil.example", "null"):
            with self.subTest(origin=origin):
                response = self.client.get("/api/v1/core/health/", HTTP_ORIGIN=origin)
                self.assertNotIn("Access-Control-Allow-Origin", response)

    @override_settings(CORS_ALLOWED_ORIGINS=[])
    def test_empty_allowlist_grants_no_cross_origin_access(self):
        response = self.client.get("/api/v1/core/health/", HTTP_ORIGIN=FRONTEND)
        self.assertNotIn("Access-Control-Allow-Origin", response)

    def test_json_contact_preflight_succeeds_without_writing_a_message(self):
        response = self.client.options(
            "/api/v1/contact/",
            HTTP_ORIGIN=FRONTEND,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], FRONTEND)
        self.assertIn("POST", response["Access-Control-Allow-Methods"])
        self.assertIn("content-type", response["Access-Control-Allow-Headers"])

    def test_api_errors_also_include_cors_headers(self):
        response = self.client.get("/api/v1/does-not-exist/", HTTP_ORIGIN=FRONTEND)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Access-Control-Allow-Origin"], FRONTEND)

    def test_admin_retains_csrf_protection_and_has_no_cors_access(self):
        response = Client(enforce_csrf_checks=True).post(
            "/admin/login/", {}, HTTP_ORIGIN=FRONTEND
        )
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("Access-Control-Allow-Origin", response)
