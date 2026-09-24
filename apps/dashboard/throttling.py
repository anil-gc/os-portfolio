from hashlib import sha256
from ipaddress import ip_address

from django.conf import settings
from django.core.cache import cache


LOGIN_FAILURE_LIMIT = 10
LOGIN_FAILURE_WINDOW = 300


def login_cache_key(request):
    address = request.META.get("REMOTE_ADDR", "unknown")
    if settings.DASHBOARD_TRUST_PROXY_IP:
        # Caddy must overwrite this header; never trust arbitrary forwarding chains.
        candidate = request.META.get("HTTP_X_REAL_IP", "")
        try:
            address = str(ip_address(candidate))
        except ValueError:
            pass
    return "dashboard:login:" + sha256(address.encode()).hexdigest()


def login_is_limited(request):
    return cache.get(login_cache_key(request), 0) >= LOGIN_FAILURE_LIMIT


def record_login_failure(request):
    key = login_cache_key(request)
    if not cache.add(key, 1, timeout=LOGIN_FAILURE_WINDOW):
        try:
            cache.incr(key)
        except ValueError:
            # The window can expire between add and incr.
            cache.add(key, 1, timeout=LOGIN_FAILURE_WINDOW)
