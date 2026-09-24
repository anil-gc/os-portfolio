from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.projects.models import Project
from .access import DashboardAccessMixin
from .overview import can_view
from .project_forms import ProjectForm


class ProjectWorkspaceMixin(DashboardAccessMixin):
    model = Project

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            public_portfolio_url=settings.DASHBOARD_PUBLIC_SITE_URL,
            dashboard_section="projects", **kwargs,
        )

    def get_success_url(self):
        return reverse("dashboard:project-list" if can_view(self.request.user, Project) else "dashboard:home")


class ProjectListView(ProjectWorkspaceMixin, ListView):
    template_name = "dashboard/projects/list.html"
    context_object_name = "projects"
    paginate_by = 10

    @property
    def permission_required(self):
        return "projects.change_project" if self.request.user.has_perm("projects.change_project") else "projects.view_project"

    def get_queryset(self):
        self.query = self.request.GET.get("q", "").strip()[:160]
        self.status = self.request.GET.get("status", "")
        if self.status not in ("published", "draft"):
            self.status = ""
        queryset = super().get_queryset().defer("description")
        if self.query:
            queryset = queryset.filter(Q(title__icontains=self.query) | Q(category__icontains=self.query))
        if self.status:
            queryset = queryset.filter(is_published=self.status == "published")
        return queryset.order_by("sort_order", "pk")

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            query=self.query, status_filter=self.status,
            filter_query=urlencode({"q": self.query, "status": self.status}), **kwargs,
        )


class ProjectSaveMixin(ProjectWorkspaceMixin):
    form_class = ProjectForm
    template_name = "dashboard/projects/form.html"

    def form_valid(self, form):
        creating = form.instance.pk is None
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except IntegrityError:
            # A concurrent save can claim a slug after ModelForm validation.
            if Project.objects.filter(slug=form.cleaned_data["slug"]).exclude(pk=self.object.pk if self.object else None).exists():
                form.add_error("slug", "A project with this slug already exists. Choose another slug.")
                return self.form_invalid(form)
            raise
        messages.success(self.request, f'Project "{self.object.title}" {"created" if creating else "updated"}.')
        return response


class ProjectCreateView(ProjectSaveMixin, CreateView):
    permission_required = "projects.add_project"


class ProjectUpdateView(ProjectSaveMixin, UpdateView):
    permission_required = "projects.change_project"


class ProjectDeleteView(ProjectWorkspaceMixin, DeleteView):
    permission_required = "projects.delete_project"
    template_name = "dashboard/projects/confirm_delete.html"
    http_method_names = ["get", "post", "head", "options"]

    def form_valid(self, form):
        title = self.object.title
        response = super().form_valid(form)
        messages.success(self.request, f'Project "{title}" deleted.')
        return response
