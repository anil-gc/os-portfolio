from rest_framework import serializers
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("name", "headline", "location", "intro", "bio", "about", "email", "github_url", "linkedin_url", "avatar_url", "available", "is_demo")
