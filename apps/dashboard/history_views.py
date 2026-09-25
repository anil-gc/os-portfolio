"""Shared page behavior for three small content modules; each keeps its own form and routes."""

from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.certificates.models import Certificate
from apps.education.models import Education
from apps.experience.models import Experience
from .access import DashboardAccessMixin
from .history_forms import CertificateForm, EducationForm, ExperienceForm
from .overview import can_view


class EntryWorkspaceMixin(DashboardAccessMixin):
    @property
    def permission_required(self):
        opts = self.model._meta
        change = f"{opts.app_label}.change_{opts.model_name}"
        return change if self.request.user.has_perm(change) else f"{opts.app_label}.view_{opts.model_name}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        opts = self.model._meta
        context.update(
            public_portfolio_url=settings.DASHBOARD_PUBLIC_SITE_URL,
            dashboard_section=self.section, section_title=self.section_title,
            entry_label=self.entry_label, section_icon=self.section_icon,
            section_description=self.section_description,
            empty_title=f"No {self.section_title.lower()} entries yet",
            list_url=reverse(f"dashboard:{self.route_name}-list"),
            create_url=reverse(f"dashboard:{self.route_name}-create"),
            cancel_url=self.get_success_url(),
            can_add=self.request.user.has_perm(f"{opts.app_label}.add_{opts.model_name}"),
            can_change=self.request.user.has_perm(f"{opts.app_label}.change_{opts.model_name}"),
            can_delete=self.request.user.has_perm(f"{opts.app_label}.delete_{opts.model_name}"),
        )
        return context

    def get_success_url(self):
        return reverse(f"dashboard:{self.route_name}-list" if can_view(self.request.user, self.model) else "dashboard:home")


class EntryListView(ListView):
    template_name = "dashboard/history/list.html"
    paginate_by = 10

    def get_queryset(self):
        self.query = self.request.GET.get("q", "").strip()[:160]
        self.status = self.request.GET.get("status", "")
        if self.status not in ("published", "draft"):
            self.status = ""
        queryset = super().get_queryset().defer("description")
        if self.query:
            queryset = queryset.filter(
                Q(**{f"{self.title_field}__icontains": self.query}) |
                Q(**{f"{self.subtitle_field}__icontains": self.query})
            )
        if self.status:
            queryset = queryset.filter(is_published=self.status == "published")
        return queryset.order_by("sort_order", "pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            query=self.query, status_filter=self.status,
            filter_query=urlencode({"q": self.query, "status": self.status}),
            entries=[{
                "object": obj, "title": getattr(obj, self.title_field),
                "subtitle": getattr(obj, self.subtitle_field),
                "edit_url": reverse(f"dashboard:{self.route_name}-update", args=[obj.pk]),
                "delete_url": reverse(f"dashboard:{self.route_name}-delete", args=[obj.pk]),
            } for obj in context["object_list"]],
        )
        return context


class EntrySaveMixin:
    template_name = "dashboard/history/form.html"

    def get_form_class(self):
        return self.entry_form_class

    def form_valid(self, form):
        creating = form.instance.pk is None
        response = super().form_valid(form)
        messages.success(self.request, f'{self.entry_label.capitalize()} "{self.object}" {"created" if creating else "updated"}.')
        return response


class EntryDeleteView(DeleteView):
    template_name = "dashboard/history/confirm_delete.html"
    http_method_names = ["get", "post", "head", "options"]

    def form_valid(self, form):
        name = str(self.object)
        response = super().form_valid(form)
        messages.success(self.request, f'{self.entry_label.capitalize()} "{name}" deleted.')
        return response


class ExperienceWorkspace(EntryWorkspaceMixin):
    model = Experience
    entry_form_class = ExperienceForm
    section = route_name = "experience"
    section_title = "Experience"
    entry_label = "experience"
    section_icon = "briefcase"
    section_description = "Tell the story of your work, one role at a time."
    title_field, subtitle_field = "role", "company"


class ExperienceListView(ExperienceWorkspace, EntryListView):
    pass


class ExperienceCreateView(ExperienceWorkspace, EntrySaveMixin, CreateView):
    permission_required = "experience.add_experience"


class ExperienceUpdateView(ExperienceWorkspace, EntrySaveMixin, UpdateView):
    permission_required = "experience.change_experience"


class ExperienceDeleteView(ExperienceWorkspace, EntryDeleteView):
    permission_required = "experience.delete_experience"


class EducationWorkspace(EntryWorkspaceMixin):
    model = Education
    entry_form_class = EducationForm
    section = route_name = "education"
    section_title = "Education"
    entry_label = "education"
    section_icon = "graduation"
    section_description = "Share the studies and qualifications that shaped your path."
    title_field, subtitle_field = "degree", "institution"


class EducationListView(EducationWorkspace, EntryListView):
    pass


class EducationCreateView(EducationWorkspace, EntrySaveMixin, CreateView):
    permission_required = "education.add_education"


class EducationUpdateView(EducationWorkspace, EntrySaveMixin, UpdateView):
    permission_required = "education.change_education"


class EducationDeleteView(EducationWorkspace, EntryDeleteView):
    permission_required = "education.delete_education"


class CertificateWorkspace(EntryWorkspaceMixin):
    model = Certificate
    entry_form_class = CertificateForm
    section = "certificates"
    route_name = "certificate"
    section_title = "Certificates"
    entry_label = "certificate"
    section_icon = "award"
    section_description = "Keep your credentials and learning milestones together."
    title_field, subtitle_field = "title", "issuer"


class CertificateListView(CertificateWorkspace, EntryListView):
    pass


class CertificateCreateView(CertificateWorkspace, EntrySaveMixin, CreateView):
    permission_required = "certificates.add_certificate"


class CertificateUpdateView(CertificateWorkspace, EntrySaveMixin, UpdateView):
    permission_required = "certificates.change_certificate"


class CertificateDeleteView(CertificateWorkspace, EntryDeleteView):
    permission_required = "certificates.delete_certificate"
