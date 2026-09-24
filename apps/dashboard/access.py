from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


class DashboardAccessMixin(AccessMixin):
    """Require active staff and, when supplied, existing model permissions."""

    login_url = "dashboard:login"
    permission_required = ()

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        permissions = self.permission_required
        if isinstance(permissions, str):
            permissions = (permissions,)
        if not (
            request.user.is_active
            and request.user.is_staff
            and request.user.has_perms(permissions)
        ):
            return render(request, "dashboard/forbidden.html", status=403)
        return super().dispatch(request, *args, **kwargs)
