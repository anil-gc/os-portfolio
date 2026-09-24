from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Portfolio workspace"
admin.site.site_title = "Portfolio admin"
admin.site.index_title = "Content and messages"

urlpatterns = [
    path("dashboard/", include("apps.dashboard.urls")),
    path("admin/", admin.site.urls),
    path("api/v1/", include("config.api_urls", namespace="v1")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
