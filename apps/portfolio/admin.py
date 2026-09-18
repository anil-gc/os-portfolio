from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request):
        return super().has_add_permission(request) and not Profile.objects.exists()
