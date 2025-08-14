from rest_framework import serializers

from users.models import User


class ResponseSocialUserSignUpSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=4096)


class SocialUserSignUpSerializer(serializers.Serializer):
    provider = serializers.CharField()
    code = serializers.CharField()
    redirect_uri = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    remote_addr = serializers.SerializerMethodField()
    has_recurring_subscription = serializers.SerializerMethodField()
    subscription_start_date = serializers.DateTimeField(allow_null=True, source="subscription_boundaries.start_date")
    subscription_end_date = serializers.DateTimeField(allow_null=True, source="subscription_boundaries.end_date")

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "birthdate",
            "avatar_slug",
            "remote_addr",
            "has_accepted_data_consent",
            "has_recurring_subscription",
            "subscription_start_date",
            "subscription_end_date",
            "rhash",
        ]
        read_only_fields = fields

    def get_remote_addr(self, obj: User) -> str:
        return self.context["request"].META["REMOTE_ADDR"]

    def get_has_recurring_subscription(self, obj: User) -> bool:
        return obj.has_recurring_subscription()


class UserUpdateSerializer(serializers.ModelSerializer):
    has_accepted_data_consent = serializers.BooleanField(allow_null=True, required=False)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "birthdate",
            "avatar_slug",
            "has_accepted_data_consent",
        ]


class UserSignUpSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=70)
    first_name = serializers.CharField(max_length=150, allow_null=True, required=False)
    last_name = serializers.CharField(max_length=150, allow_null=True, required=False)


class UserSignInSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=70)


class UserBonusesSerializer(serializers.Serializer):
    bonuses = serializers.IntegerField(min_value=0)


class UserCommentTokenSerializer(serializers.Serializer):
    signature = serializers.CharField()
    user_json_base64 = serializers.CharField()
    current_time_ms = serializers.CharField()


class UserRecurrentInfoSerializer(serializers.Serializer):
    product_name = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    next_charge_date = serializers.DateTimeField(allow_null=True)
    card_mask = serializers.CharField()
