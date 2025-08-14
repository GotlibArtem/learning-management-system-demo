from typing import Any

from rest_framework import serializers
from rest_social_auth.serializers import JWTSlidingSerializer


class SlidingTokenObtainByUsernameCodeSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=70)
    code = serializers.CharField(max_length=100)
    device_uuid = serializers.CharField(max_length=128, default="")


class ResponseSlidingTokenObtainByUsernameCodeSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=4096)


class SocialJWTSlidingSerializer(JWTSlidingSerializer):
    def get_token(self, obj: Any) -> str:
        return str(self.get_token_instance())
