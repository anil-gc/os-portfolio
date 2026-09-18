from django.urls import path
from .views import MessageCreateView

app_name = "contact"

urlpatterns = [
    path("", MessageCreateView.as_view(), name="create"),
]
