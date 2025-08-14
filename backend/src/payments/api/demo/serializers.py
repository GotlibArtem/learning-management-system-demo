from decimal import Decimal

from rest_framework import serializers

from payments.models import (
    PaymentMethod,
    PaymentProvider,
    PaymentSource,
    PaymentStatus,
    RecurrentChargeStatus,
    RecurrentStatus,
)


class IncomingUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone = serializers.CharField(allow_null=True, allow_blank=True)
    first_name = serializers.CharField(allow_null=True, allow_blank=True)
    last_name = serializers.CharField(allow_null=True, allow_blank=True)
    rhash = serializers.CharField(allow_null=True, allow_blank=True, required=False)


class IncomingProductSerializer(serializers.Serializer):
    shop_id = serializers.CharField()
    lms_id = serializers.CharField(allow_null=True, allow_blank=True)
    name = serializers.CharField()


class IncomingChargeAttemptSerializer(serializers.Serializer):
    pan = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    token = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    amount = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    currency = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    card_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    success = serializers.BooleanField(required=False, allow_null=True, default=True)
    exp_date = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    rebill_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    error_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    payment_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class IncomingRecurrentSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=RecurrentStatus.choices)
    charge_token = serializers.CharField()
    charge_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    provider = serializers.ChoiceField(choices=PaymentProvider.choices)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    next_charge_date = serializers.DateTimeField(required=False, allow_null=True)
    last_attempt_charge_date = serializers.DateTimeField(required=False, allow_null=True)
    last_attempt_charge_status = serializers.ChoiceField(choices=RecurrentChargeStatus.choices, required=False, allow_null=True)
    attempts_charge = IncomingChargeAttemptSerializer(many=True, required=False, allow_null=True)
    attempts_charge_raw = serializers.ListField(child=serializers.JSONField(), required=False, allow_null=True)


class IncomingPaymentSerializer(serializers.Serializer):
    payment_id = serializers.CharField()
    order_id = serializers.CharField()
    user = IncomingUserSerializer()
    product = IncomingProductSerializer()
    is_recurrent = serializers.BooleanField(default=False, required=False)
    recurrent = IncomingRecurrentSerializer(required=False, allow_null=True)
    source = serializers.ChoiceField(choices=PaymentSource.choices, default=PaymentSource.SITE, required=False, allow_null=True)  # type: ignore
    provider = serializers.ChoiceField(choices=PaymentProvider.choices)
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    status = serializers.ChoiceField(choices=PaymentStatus.choices)
    paid_at = serializers.DateTimeField()
    order_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_price = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), required=False, allow_null=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    bonus_applied = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), required=False, allow_null=True)
    promo_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    provider_response = serializers.JSONField(required=False, allow_null=True)
