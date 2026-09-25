from rest_framework import serializers
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url
        return obj.avatar_url

    class Meta:
        model = Profile
        fields = ("name", "headline", "location", "intro", "bio", "about", "email", "github_url", "linkedin_url", "avatar_url", "available", "is_demo")
