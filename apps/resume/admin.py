from django.contrib import admin
from apps.core.content import PublishedContentAdmin
from .models import Resume


@admin.register(Resume)
class ResumeAdmin(PublishedContentAdmin):
    search_fields = ("title",)
