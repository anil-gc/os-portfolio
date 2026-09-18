from django.urls import path
from .views import SiteView

app_name = "portfolio"

urlpatterns = [
    path("site/", SiteView.as_view(), name="site"),
]
