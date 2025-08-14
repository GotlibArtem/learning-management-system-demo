from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.views import APIView

from app.api.request import AuthenticatedRequest
from bonuses.api.demo.permissions import BonusIntegrationPermission
from bonuses.api.demo.serializers import BonusAccountSerializer, BonusChangeSerializer, BonusEmailSerializer
from bonuses.models import BonusAccount, BonusTransaction, BonusTransactionType
from bonuses.services import BonusAccountGetter, BonusTransactionCreator


class BonusAccountByEmailView(APIView):
    permission_classes = [BonusIntegrationPermission]
    queryset = BonusAccount.objects.all()

    @extend_schema(
        request=BonusEmailSerializer,
        responses={HTTP_200_OK: BonusAccountSerializer},
        description="Get bonus account info by user email.",
    )
    def get(self, request: AuthenticatedRequest) -> Response:
        serializer = BonusEmailSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        bonus_account = BonusAccountGetter(email=serializer.validated_data["email"])()

        return Response(BonusAccountSerializer(bonus_account).data, status=HTTP_200_OK)


class BonusEarnView(APIView):
    permission_classes = [BonusIntegrationPermission]
    queryset = BonusTransaction.objects.all()

    @extend_schema(
        request=BonusChangeSerializer,
        responses={HTTP_201_CREATED: BonusAccountSerializer},
        description="Earn bonuses for user by email.",
    )
    def post(self, request: AuthenticatedRequest) -> Response:
        serializer = BonusChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bonus_account = BonusTransactionCreator(
            email=serializer.validated_data["email"],
            amount=serializer.validated_data["amount"],
            transaction_type=BonusTransactionType.EARNED,
            reason=serializer.validated_data["reason"],
            created_by=request.user,
        )()

        return Response(BonusAccountSerializer(bonus_account).data, status=HTTP_201_CREATED)


class BonusSpendView(APIView):
    permission_classes = [BonusIntegrationPermission]
    queryset = BonusTransaction.objects.all()

    @extend_schema(
        request=BonusChangeSerializer,
        responses={HTTP_201_CREATED: BonusAccountSerializer},
        description="Spend bonuses for user by email.",
    )
    def post(self, request: AuthenticatedRequest) -> Response:
        serializer = BonusChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bonus_account = BonusTransactionCreator(
            email=serializer.validated_data["email"],
            amount=serializer.validated_data["amount"],
            transaction_type=BonusTransactionType.SPENT,
            reason=serializer.validated_data["reason"],
            created_by=request.user,
        )()

        return Response(BonusAccountSerializer(bonus_account).data, status=HTTP_201_CREATED)
