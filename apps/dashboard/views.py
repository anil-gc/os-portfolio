from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from .access import DashboardAccessMixin
from .forms import StaffAuthenticationForm
from .overview import get_overview
from .throttling import LOGIN_FAILURE_WINDOW, login_is_limited, record_login_failure


@method_decorator(never_cache, name="dispatch")
class DashboardLoginView(LoginView):
    template_name = "dashboard/login.html"
    authentication_form = StaffAuthenticationForm
    next_page = reverse_lazy("dashboard:home")

    def get_success_url(self):
        destination = super().get_success_url()
        # A bookmarked login URL must not redirect an already signed-in user to itself.
        if destination.split("?", 1)[0] == self.request.path:
            return str(self.next_page)
        return destination

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_active and request.user.is_staff:
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if login_is_limited(request):
            form = self.get_form_class()(request=request)
            response = self.render_to_response(
                self.get_context_data(form=form, rate_limited=True), status=429
            )
            response["Retry-After"] = str(LOGIN_FAILURE_WINDOW)
            return response
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        record_login_failure(self.request)
        return super().form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "You're signed in. Welcome to your workspace.")
        return response


class DashboardLogoutView(DashboardAccessMixin, LogoutView):
    next_page = reverse_lazy("dashboard:login")

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "You've been signed out.")
        return response


class DashboardHomeView(DashboardAccessMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            public_portfolio_url=settings.DASHBOARD_PUBLIC_SITE_URL,
            **get_overview(self.request.user),
            **kwargs,
        )
