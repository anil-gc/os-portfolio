from .base import *  # noqa: F401,F403


DEBUG = env.bool("DJANGO_DEBUG", default=True)  # noqa: F405
DASHBOARD_PUBLIC_SITE_URL = env(  # noqa: F405
    "DASHBOARD_PUBLIC_SITE_URL", default="http://127.0.0.1:5173/"
)
ALLOWED_HOSTS = env.list(  # noqa: F405
    "DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "[::1]"]
)
