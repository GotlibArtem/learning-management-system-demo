from rest_framework import serializers


class MindboxPostCheckoutMagicLinkSerializer(serializers.Serializer):
    authentication_link = serializers.URLField()


class MindboxPostCheckoutMagicLinkCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
