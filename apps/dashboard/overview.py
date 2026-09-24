"""Read-only overview data, using the same model permissions as Django admin."""

from django.db.models import Count, Q
from django.urls import reverse

from apps.certificates.models import Certificate
from apps.contact.models import Message
from apps.experience.models import Experience
from apps.portfolio.models import Profile
from apps.projects.models import Project
from apps.skills.models import Skill


def can_view(user, model):
    opts = model._meta
    return any(user.has_perm(f"{opts.app_label}.{action}_{opts.model_name}") for action in ("view", "change"))


def get_overview(user):
    stats, actions = [], []
    context = {"stats": stats, "quick_actions": actions}
    content = (
        (Project, "Total projects", "folder", "blue", "Add project"),
        (Skill, "Total skills", "code", "lilac", "Add skill"),
        (Certificate, "Total certificates", "award", "amber", "Add certificate"),
        (Experience, "Experience entries", "briefcase", "green", None),
    )
    for model, label, icon, tone, action in content:
        opts = model._meta
        if can_view(user, model):
            counts = model.objects.aggregate(total=Count("pk"), published=Count("pk", filter=Q(is_published=True)))
            drafts = counts["total"] - counts["published"]
            stats.append({
                "label": label, "icon": icon, "tone": tone, "total": counts["total"],
                "detail": f'{counts["published"]} published · {drafts} draft' + ("" if drafts == 1 else "s"),
                "url": reverse("dashboard:project-list" if model is Project else f"admin:{opts.app_label}_{opts.model_name}_changelist"),
            })
        if action and user.has_perm(f"{opts.app_label}.add_{opts.model_name}"):
            actions.append({"label": action, "icon": icon, "url": reverse("dashboard:project-create" if model is Project else f"admin:{opts.app_label}_{opts.model_name}_add")})

    context["show_projects"] = can_view(user, Project)
    if context["show_projects"]:
        context["recent_projects"] = Project.objects.order_by("-updated_at", "-pk").only(
            "title", "image_url", "updated_at", "is_published", "featured"
        )[:4]

    context["show_messages"] = can_view(user, Message)
    if context["show_messages"]:
        counts = Message.objects.aggregate(total=Count("pk"), unread=Count("pk", filter=Q(is_read=False)))
        stats.append({
            "label": "Contact messages", "icon": "mail", "tone": "blue", "total": counts["total"],
            "detail": f'{counts["unread"]} unread', "url": reverse("admin:contact_message_changelist"),
        })
        context["unread_messages"] = counts["unread"]
        # Do not fetch email addresses or message bodies for the overview.
        context["recent_messages"] = Message.objects.order_by("-created_at", "-pk").only(
            "name", "subject", "created_at", "is_read"
        )[:4]

    if user.has_perm("portfolio.change_profile") or user.has_perm("portfolio.add_profile"):
        profile_pk = Profile.objects.values_list("pk", flat=True).first()
        if profile_pk is not None and user.has_perm("portfolio.change_profile"):
            actions.append({"label": "Edit profile", "icon": "user", "url": reverse("admin:portfolio_profile_change", args=[profile_pk])})
        elif profile_pk is None and user.has_perm("portfolio.add_profile"):
            actions.append({"label": "Set up profile", "icon": "user", "url": reverse("admin:portfolio_profile_add")})
    return context
