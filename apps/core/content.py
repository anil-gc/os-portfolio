from django.contrib import admin
from django.db import models

from .models import TimeStampedModel


class PublishedContent(TimeStampedModel):
    is_published = models.BooleanField(default=False, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ("sort_order", "pk")


class PublishedContentAdmin(admin.ModelAdmin):
    list_display = ("__str__", "is_published", "sort_order")
    list_editable = ("is_published", "sort_order")
    list_filter = ("is_published",)
    readonly_fields = ("created_at", "updated_at")
