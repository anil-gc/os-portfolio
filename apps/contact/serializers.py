from rest_framework import serializers
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    website = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Message
        fields = ("name", "email", "subject", "message", "website")
        extra_kwargs = {"message": {"min_length": 10}}

    def validate_website(self, value):
        if value:
            raise serializers.ValidationError("Unable to accept this submission.")
        return value

    def create(self, validated_data):
        validated_data.pop("website", None)
        return super().create(validated_data)
