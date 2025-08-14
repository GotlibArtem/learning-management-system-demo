from rest_framework import serializers


class OrderCheckoutUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    first_name = serializers.CharField(allow_null=True, allow_blank=True)
    last_name = serializers.CharField(allow_null=True, allow_blank=True)
    rhash = serializers.CharField(allow_null=True, allow_blank=True, required=False)


class OrderCheckoutProductSerializer(serializers.Serializer):
    shop_id = serializers.CharField()
    lms_id = serializers.CharField(allow_null=True, allow_blank=True)
    name = serializers.CharField()


class OrderCheckoutDataSerializer(serializers.Serializer):
    order_id = serializers.CharField()
    user = OrderCheckoutUserSerializer()
    start_date = serializers.DateField()
    end_date = serializers.DateField(allow_null=True)
    product = OrderCheckoutProductSerializer()


class OrderCheckoutSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    event_type = serializers.CharField()
    event_time = serializers.DateTimeField()
    data = OrderCheckoutDataSerializer()  # type: ignore[assignment]


class OrderRefundDataSerializer(serializers.Serializer):
    order_id = serializers.CharField()


class OrderRefundSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    event_type = serializers.CharField()
    event_time = serializers.DateTimeField()
    data = OrderRefundDataSerializer()  # type: ignore[assignment]


class PromoAccessUserSerializer(serializers.Serializer):
    username = serializers.EmailField()


class PromoAccessDataSerializer(serializers.Serializer):
    user = PromoAccessUserSerializer()


class PromoAccessSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    event_type = serializers.CharField()
    event_time = serializers.DateTimeField()
    data = PromoAccessDataSerializer()  # type: ignore[assignment]
