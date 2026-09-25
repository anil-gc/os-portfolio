"""Private inbox over the same records created by the public contact API."""

from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.functions import Substr
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DeleteView, DetailView, ListView

from apps.contact.models import Message
from .access import DashboardAccessMixin


class MessageWorkspaceMixin(DashboardAccessMixin):
    model = Message

    @property
    def permission_required(self):
        return "contact.change_message" if self.request.user.has_perm("contact.change_message") else "contact.view_message"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            dashboard_section="messages", section_title="Messages",
            public_portfolio_url=settings.DASHBOARD_PUBLIC_SITE_URL,
            can_change=self.request.user.has_perm("contact.change_message"),
            can_delete=self.request.user.has_perm("contact.delete_message"),
        )
        return context


class MessageListView(MessageWorkspaceMixin, ListView):
    template_name = "dashboard/messages/list.html"
    context_object_name = "entries"
    paginate_by = 10
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        self.query = self.request.GET.get("q", "").strip()[:160]
        self.status = self.request.GET.get("status", "")
        if self.status not in ("read", "unread"):
            self.status = ""
        # Only fetch a short preview for this page, not full private message bodies.
        queryset = Message.objects.defer("message").annotate(preview=Substr("message", 1, 181))
        if self.query:
            queryset = queryset.filter(Q(name__icontains=self.query) | Q(email__icontains=self.query) | Q(subject__icontains=self.query))
        if self.status:
            queryset = queryset.filter(is_read=self.status == "read")
        return queryset.order_by("-created_at", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            query=self.query, status_filter=self.status,
            filter_query=urlencode({"q": self.query, "status": self.status}),
            inbox_counts=Message.objects.aggregate(total=Count("pk"), unread=Count("pk", filter=Q(is_read=False))),
        )
        return context


class MessageDetailView(MessageWorkspaceMixin, DetailView):
    template_name = "dashboard/messages/detail.html"
    context_object_name = "entry"
    http_method_names = ["get", "head", "options"]


class MessageStatusView(MessageDetailView):
    permission_required = "contact.change_message"
    http_method_names = ["post", "options"]

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        status = request.POST.get("status")
        if status not in ("read", "unread"):
            return self.render_to_response(self.get_context_data(status_error="Choose Read or Unread."), status=400)
        # Explicit state is safe to repeat and never updates the visitor's text.
        Message.objects.filter(pk=self.object.pk).update(is_read=status == "read", updated_at=timezone.now())
        messages.success(request, f"Message marked as {status}.")
        return redirect("dashboard:message-detail", pk=self.object.pk)


class MessageDeleteView(MessageWorkspaceMixin, DeleteView):
    template_name = "dashboard/messages/confirm_delete.html"
    context_object_name = "entry"
    success_url = reverse_lazy("dashboard:message-list")
    http_method_names = ["get", "post", "head", "options"]

    @property
    def permission_required(self):
        # Deletion permission alone must not reveal private content.
        return (super().permission_required, "contact.delete_message")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Message deleted.")
        return response
