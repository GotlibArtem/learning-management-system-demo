from rest_framework import serializers

from bonuses.models import BonusAccount


class BonusEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class BonusChangeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    amount = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=512, required=False, allow_blank=True)


class BonusAccountSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = BonusAccount
        fields = ("email", "balance", "is_active")
