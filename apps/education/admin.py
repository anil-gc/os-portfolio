from django.contrib import admin
from apps.core.content import PublishedContentAdmin
from .models import Education


@admin.register(Education)
class EducationAdmin(PublishedContentAdmin):
    search_fields = ("degree",)
