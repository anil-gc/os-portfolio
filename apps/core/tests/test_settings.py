import json
import os
import secrets
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase


SETTINGS_PROBE = """
import importlib
import json
import sys
from unittest.mock import patch

with patch('environ.Env.read_env'):
    config = importlib.import_module(sys.argv[1])

print(json.dumps({
    'debug': config.DEBUG,
    'hosts': config.ALLOWED_HOSTS,
    'proxy_header': getattr(config, 'SECURE_PROXY_SSL_HEADER', None),
    'ssl_redirect': getattr(config, 'SECURE_SSL_REDIRECT', False),
    'session_secure': getattr(config, 'SESSION_COOKIE_SECURE', False),
    'csrf_secure': getattr(config, 'CSRF_COOKIE_SECURE', False),
    'hsts_subdomains': getattr(config, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False),
    'hsts_preload': getattr(config, 'SECURE_HSTS_PRELOAD', False),
    'renderers': config.REST_FRAMEWORK.get('DEFAULT_RENDERER_CLASSES'),
}))
"""


class SettingsTests(SimpleTestCase):
    def probe(self, module, overrides=None):
        # Fresh imports and no .env isolate startup behavior from developer settings.
        environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("DJANGO_") and key != "DATABASE_URL"
        }
        environment.update(overrides or {})
        return subprocess.run(
            [sys.executable, "-c", SETTINGS_PROBE, f"config.settings.{module}"],
            env=environment,
            cwd=settings.BASE_DIR,
            capture_output=True,
            text=True,
            timeout=20,
        )

    def production_environment(self):
        return {
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(64),
            "DJANGO_ALLOWED_HOSTS": "api.example.com",
            "DATABASE_URL": "sqlite:///:memory:",
        }

    def test_local_defaults_and_explicit_debug_override(self):
        for override, expected in (({}, True), ({"DJANGO_DEBUG": "False"}, False)):
            with self.subTest(override=override):
                result = self.probe("local", override)
                self.assertEqual(result.returncode, 0, result.stderr)
                data = json.loads(result.stdout)
                self.assertEqual(data["debug"], expected)
                self.assertIn("localhost", data["hosts"])

    def test_production_requires_explicit_configuration(self):
        for key in ("DJANGO_SECRET_KEY", "DJANGO_ALLOWED_HOSTS", "DATABASE_URL"):
            with self.subTest(missing=key):
                environment = self.production_environment()
                del environment[key]
                result = self.probe("production", environment)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ImproperlyConfigured", result.stderr)
                self.assertIn(key, result.stderr)

    def test_production_rejects_weak_secrets_and_wildcard_hosts(self):
        for override in (
            {"DJANGO_SECRET_KEY": "change-me"},
            {"DJANGO_SECRET_KEY": "a" * 64},
            {"DJANGO_SECRET_KEY": "django-insecure-" + secrets.token_urlsafe(64)},
            {"DJANGO_ALLOWED_HOSTS": "*"},
            {"DJANGO_ALLOWED_HOSTS": ""},
        ):
            with self.subTest(setting=next(iter(override))):
                result = self.probe("production", self.production_environment() | override)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ImproperlyConfigured", result.stderr)

    def test_production_enforces_https_without_implicitly_trusting_a_proxy(self):
        environment = self.production_environment() | {"DJANGO_DEBUG": "True"}
        result = self.probe("production", environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertFalse(data["debug"])
        self.assertIsNone(data["proxy_header"])
        self.assertTrue(data["ssl_redirect"])
        self.assertTrue(data["session_secure"])
        self.assertTrue(data["csrf_secure"])
        self.assertFalse(data["hsts_subdomains"])
        self.assertFalse(data["hsts_preload"])
        self.assertEqual(data["renderers"], ["rest_framework.renderers.JSONRenderer"])

    def test_trusted_proxy_requires_explicit_opt_in(self):
        environment = self.production_environment() | {
            "DJANGO_TRUST_PROXY_SSL_HEADER": "True"
        }
        result = self.probe("production", environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout)["proxy_header"],
            ["HTTP_X_FORWARDED_PROTO", "https"],
        )
