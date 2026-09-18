from django.contrib import admin
from apps.core.content import PublishedContentAdmin
from .models import Project


@admin.register(Project)
class ProjectAdmin(PublishedContentAdmin):
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
