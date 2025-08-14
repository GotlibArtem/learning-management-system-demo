from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.api.demo.permissions import PaymentIntegrationPermission
from payments.api.demo.serializers import IncomingPaymentSerializer
from payments.models import Payment
from payments.services import PaymentFromShopProcessor
from product_access.api.demo.decorators import dead_letter_creation


class PaymentFromShopView(APIView):
    permission_classes = [PaymentIntegrationPermission]
    queryset = Payment.objects.all()

    @extend_schema(
        request=IncomingPaymentSerializer,
        responses={201: None},
    )
    @dead_letter_creation(event_type="incoming-payment-from-shop")
    def post(self, request: Request) -> Response:
        serializer = IncomingPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        PaymentFromShopProcessor(serializer.validated_data)()

        return Response(status=status.HTTP_201_CREATED)
