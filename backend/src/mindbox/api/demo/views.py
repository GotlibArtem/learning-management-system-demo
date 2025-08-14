from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from mindbox.api.demo.permissions import MindboxIntegrationPermission
from mindbox.api.demo.serializers import MindboxPostCheckoutMagicLinkCreateSerializer, MindboxPostCheckoutMagicLinkSerializer
from mindbox.services import MindboxMagicLinkGenerator
from users.models import User


class MindboxPostCheckoutMagicLinkView(APIView):
    permission_classes = [MindboxIntegrationPermission]
    queryset = User.objects.all()

    @extend_schema(
        request=MindboxPostCheckoutMagicLinkCreateSerializer,
        responses=MindboxPostCheckoutMagicLinkSerializer,
    )
    def post(self, request: Request) -> Response:
        serializer = MindboxPostCheckoutMagicLinkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_link = MindboxMagicLinkGenerator(username=serializer.validated_data["email"])()
        response_serializer = MindboxPostCheckoutMagicLinkSerializer(
            {"authentication_link": auth_link},
        )
        return Response(data=response_serializer.data)
