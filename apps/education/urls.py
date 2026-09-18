from django.urls import path
from .views import EducationListView

app_name = "education"

urlpatterns = [
    path("", EducationListView.as_view(), name="list"),
]
