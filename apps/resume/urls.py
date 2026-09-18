from django.urls import path
from .views import ResumeListView

app_name = "resume"

urlpatterns = [
    path("", ResumeListView.as_view(), name="list"),
]
