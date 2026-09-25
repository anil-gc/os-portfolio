from django.urls import path

from .views import DashboardHomeView, DashboardLoginView, DashboardLogoutView
from .project_views import ProjectCreateView, ProjectDeleteView, ProjectListView, ProjectUpdateView
from .skill_views import SkillCreateView, SkillDeleteView, SkillListView, SkillUpdateView
from . import history_views
from .profile_views import ProfileView
from .message_views import MessageDeleteView, MessageDetailView, MessageListView, MessageStatusView


app_name = "dashboard"

urlpatterns = [
    path("messages/", MessageListView.as_view(), name="message-list"),
    path("messages/<int:pk>/", MessageDetailView.as_view(), name="message-detail"),
    path("messages/<int:pk>/status/", MessageStatusView.as_view(), name="message-status"),
    path("messages/<int:pk>/delete/", MessageDeleteView.as_view(), name="message-delete"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("", DashboardHomeView.as_view(), name="home"),
    path("login/", DashboardLoginView.as_view(), name="login"),
    path("logout/", DashboardLogoutView.as_view(), name="logout"),
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("projects/new/", ProjectCreateView.as_view(), name="project-create"),
    path("projects/<int:pk>/edit/", ProjectUpdateView.as_view(), name="project-update"),
    path("projects/<int:pk>/delete/", ProjectDeleteView.as_view(), name="project-delete"),
    path("skills/", SkillListView.as_view(), name="skill-list"),
    path("skills/new/", SkillCreateView.as_view(), name="skill-create"),
    path("skills/<int:pk>/edit/", SkillUpdateView.as_view(), name="skill-update"),
    path("skills/<int:pk>/delete/", SkillDeleteView.as_view(), name="skill-delete"),
    path("experience/", history_views.ExperienceListView.as_view(), name="experience-list"),
    path("experience/new/", history_views.ExperienceCreateView.as_view(), name="experience-create"),
    path("experience/<int:pk>/edit/", history_views.ExperienceUpdateView.as_view(), name="experience-update"),
    path("experience/<int:pk>/delete/", history_views.ExperienceDeleteView.as_view(), name="experience-delete"),
    path("education/", history_views.EducationListView.as_view(), name="education-list"),
    path("education/new/", history_views.EducationCreateView.as_view(), name="education-create"),
    path("education/<int:pk>/edit/", history_views.EducationUpdateView.as_view(), name="education-update"),
    path("education/<int:pk>/delete/", history_views.EducationDeleteView.as_view(), name="education-delete"),
    path("certificates/", history_views.CertificateListView.as_view(), name="certificate-list"),
    path("certificates/new/", history_views.CertificateCreateView.as_view(), name="certificate-create"),
    path("certificates/<int:pk>/edit/", history_views.CertificateUpdateView.as_view(), name="certificate-update"),
    path("certificates/<int:pk>/delete/", history_views.CertificateDeleteView.as_view(), name="certificate-delete"),
]
