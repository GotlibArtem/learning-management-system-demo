from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from product_access.api.demo.decorators import dead_letter_creation
from product_access.api.demo.permissions import ShopIntegrationPermission
from product_access.api.demo.serializers import OrderCheckoutSerializer, OrderRefundSerializer, PromoAccessSerializer
from product_access.models import ProductAccess
from product_access.services import ProductAccessRevoker, ProductCheckoutProcessor, PromoProductCheckoutProcessor


class OrderCheckoutView(APIView):
    permission_classes = [ShopIntegrationPermission]
    queryset = ProductAccess.objects.all()

    @extend_schema(
        request=OrderCheckoutSerializer,
        responses=inline_serializer(
            "OrderCheckoutResponseSerializer",
            fields={
                "redirect_url": serializers.CharField(),
            },
        ),
    )
    @dead_letter_creation(event_type="order-checkedout")
    def post(self, request: Request) -> Response:
        serializer = OrderCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        redirect_url = ProductCheckoutProcessor(checkout_event=serializer.validated_data.copy())()
        return Response({"redirect_url": redirect_url}, status=status.HTTP_200_OK)


class OrderRefundView(APIView):
    permission_classes = [ShopIntegrationPermission]
    queryset = ProductAccess.objects.all()

    @extend_schema(
        request=OrderRefundSerializer,
        responses=None,
    )
    @dead_letter_creation(event_type="order-refunded")
    def post(self, request: Request) -> Response:
        serializer = OrderRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ProductAccessRevoker(
            order_id=serializer.validated_data["data"]["order_id"],
            access_revoke_time=serializer.validated_data["event_time"],
        )()

        return Response(status=status.HTTP_200_OK)


class PromoAccessView(APIView):
    permission_classes = [ShopIntegrationPermission]
    queryset = ProductAccess.objects.all()

    @extend_schema(
        request=PromoAccessSerializer,
        responses=inline_serializer(
            "PromoAccessResponseSerializer",
            fields={
                "redirect_url": serializers.CharField(required=False),
            },
        ),
    )
    @dead_letter_creation(event_type="promo-access")
    def post(self, request: Request) -> Response:
        serializer = PromoAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        redirect_url = PromoProductCheckoutProcessor(checkout_event=serializer.validated_data.copy())()
        return Response({"redirect_url": redirect_url}, status=status.HTTP_200_OK)
