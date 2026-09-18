from django.contrib import admin
from apps.core.content import PublishedContentAdmin
from .models import Experience


@admin.register(Experience)
class ExperienceAdmin(PublishedContentAdmin):
    search_fields = ("role",)
