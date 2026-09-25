from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from apps.portfolio.models import Profile
from apps.portfolio.serializers import ProfileSerializer
from apps.resume.models import Resume
from .access import DashboardAccessMixin
from .profile_forms import ProfileForm, ProfileResumeForm


class ProfileView(DashboardAccessMixin, TemplateView):
    template_name = "dashboard/profile/form.html"
    http_method_names = ["get", "post", "head", "options"]

    @property
    def permission_required(self):
        return "portfolio.change_profile" if Profile.objects.filter(pk=1).exists() else "portfolio.add_profile"

    def get_forms(self):
        profile = Profile.objects.filter(pk=1).first() or Profile(pk=1, is_demo=False)
        # Match SiteView's published selection; reuse an existing draft if none is public.
        resume = Resume.objects.filter(is_published=True).first() or Resume.objects.first()
        resume_permission = "resume.change_resume" if resume else "resume.add_resume"
        kwargs = {"data": self.request.POST, "files": self.request.FILES} if self.request.method == "POST" else {}
        form = ProfileForm(instance=profile, **kwargs)
        resume_form = ProfileResumeForm(instance=resume, prefix="resume", **kwargs) if self.request.user.has_perm(resume_permission) else None
        return form, resume_form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "form" not in context:
            context["form"], context["resume_form"] = self.get_forms()
        context.update(
            dashboard_section="profile", section_title="Profile / About",
            public_portfolio_url=settings.DASHBOARD_PUBLIC_SITE_URL,
            current_avatar=ProfileSerializer(Profile.objects.filter(pk=1).first() or Profile(), context={"request": self.request}).data["avatar_url"],
        )
        return context

    def post(self, request, *args, **kwargs):
        form, resume_form = self.get_forms()
        if resume_form is None and any(key.startswith("resume-") for key in (*request.POST, *request.FILES)):
            return render(request, "dashboard/forbidden.html", status=403)
        profile_valid = form.is_valid()
        resume_valid = resume_form.is_valid() if resume_form is not None else True
        if profile_valid and resume_valid:
            with transaction.atomic():
                form.save()
                if resume_form is not None and resume_form.should_save:
                    resume_form.save()
            messages.success(request, "Profile changes saved. Your portfolio will use the updated information.")
            return redirect("dashboard:profile")
        return self.render_to_response(self.get_context_data(form=form, resume_form=resume_form))
