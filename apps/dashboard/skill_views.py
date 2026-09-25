from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.skills.models import Skill
from .access import DashboardAccessMixin
from .overview import can_view
from .skill_forms import SkillForm


class SkillWorkspaceMixin(DashboardAccessMixin):
    model = Skill

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            public_portfolio_url=settings.DASHBOARD_PUBLIC_SITE_URL,
            dashboard_section="skills", **kwargs,
        )

    def get_success_url(self):
        return reverse("dashboard:skill-list" if can_view(self.request.user, Skill) else "dashboard:home")


class SkillListView(SkillWorkspaceMixin, ListView):
    template_name = "dashboard/skills/list.html"
    context_object_name = "skills"
    paginate_by = 20

    @property
    def permission_required(self):
        return "skills.change_skill" if self.request.user.has_perm("skills.change_skill") else "skills.view_skill"

    def get_queryset(self):
        self.query = self.request.GET.get("q", "").strip()[:160]
        self.status = self.request.GET.get("status", "")
        if self.status not in ("published", "draft"):
            self.status = ""
        queryset = super().get_queryset()
        if self.query:
            queryset = queryset.filter(Q(name__icontains=self.query) | Q(category__icontains=self.query))
        if self.status:
            queryset = queryset.filter(is_published=self.status == "published")
        return queryset.order_by("sort_order", "pk")

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            query=self.query, status_filter=self.status,
            filter_query=urlencode({"q": self.query, "status": self.status}), **kwargs,
        )


class SkillSaveMixin(SkillWorkspaceMixin):
    form_class = SkillForm
    template_name = "dashboard/skills/form.html"

    def form_valid(self, form):
        creating = form.instance.pk is None
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except IntegrityError:
            # The unique name may be claimed between validation and saving.
            if Skill.objects.filter(name=form.cleaned_data["name"]).exclude(pk=form.instance.pk).exists():
                form.add_error("name", "A skill with this name already exists.")
                return self.form_invalid(form)
            raise
        messages.success(self.request, f'Skill "{self.object.name}" {"created" if creating else "updated"}.')
        return response


class SkillCreateView(SkillSaveMixin, CreateView):
    permission_required = "skills.add_skill"


class SkillUpdateView(SkillSaveMixin, UpdateView):
    permission_required = "skills.change_skill"


class SkillDeleteView(SkillWorkspaceMixin, DeleteView):
    permission_required = "skills.delete_skill"
    template_name = "dashboard/skills/confirm_delete.html"
    http_method_names = ["get", "post", "head", "options"]

    def form_valid(self, form):
        name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request, f'Skill "{name}" deleted.')
        return response
