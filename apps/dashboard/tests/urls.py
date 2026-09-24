from django.http import HttpResponse
from django.urls import include, path
from django.views import View

from apps.dashboard.access import DashboardAccessMixin


class ProjectPermissionProbe(DashboardAccessMixin, View):
    permission_required = "projects.change_project"

    def get(self, request):
        return HttpResponse("Authorized")

urlpatterns = [
    path("permission-probe/", ProjectPermissionProbe.as_view()),
    path("", include("config.urls")),
]
