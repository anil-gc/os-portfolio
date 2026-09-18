from django.urls import path
from .views import ExperienceListView

app_name = "experience"

urlpatterns = [
    path("", ExperienceListView.as_view(), name="list"),
]
