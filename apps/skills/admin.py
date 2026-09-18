from django.contrib import admin
from apps.core.content import PublishedContentAdmin
from .models import Skill


@admin.register(Skill)
class SkillAdmin(PublishedContentAdmin):
    search_fields = ("name",)
