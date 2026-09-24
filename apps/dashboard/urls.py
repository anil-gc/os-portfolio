from django.urls import path

from .views import DashboardHomeView, DashboardLoginView, DashboardLogoutView
from .project_views import ProjectCreateView, ProjectDeleteView, ProjectListView, ProjectUpdateView


app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
    path("login/", DashboardLoginView.as_view(), name="login"),
    path("logout/", DashboardLogoutView.as_view(), name="logout"),
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("projects/new/", ProjectCreateView.as_view(), name="project-create"),
    path("projects/<int:pk>/edit/", ProjectUpdateView.as_view(), name="project-update"),
    path("projects/<int:pk>/delete/", ProjectDeleteView.as_view(), name="project-delete"),
]
