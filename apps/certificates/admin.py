from django.contrib import admin
from apps.core.content import PublishedContentAdmin
from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(PublishedContentAdmin):
    search_fields = ("title",)
