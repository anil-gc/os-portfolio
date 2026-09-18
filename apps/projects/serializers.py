from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("slug","title","category","summary","description","technologies","year","featured","accent","image_url","live_url","source_url")
