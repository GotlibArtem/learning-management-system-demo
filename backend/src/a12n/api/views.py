from typing import Any

from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from requests import Request
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework_simplejwt import views as jwt
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import SlidingToken
from rest_social_auth.views import SocialJWTSlidingOnlyAuthView

from a12n.api.serializers import ResponseSlidingTokenObtainByUsernameCodeSerializer, SlidingTokenObtainByUsernameCodeSerializer, SocialJWTSlidingSerializer
from a12n.api.throttling import AuthAnonRateThrottle, AuthByEmailCodeAnonRateThrottle
from a12n.services.token_by_code_generator import TokenGeneratorByCode
from users.models import User


class TokenObtainByCodeView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthByEmailCodeAnonRateThrottle]

    @extend_schema(
        request=SlidingTokenObtainByUsernameCodeSerializer,
        responses={"200": ResponseSlidingTokenObtainByUsernameCodeSerializer},
        description="Obtain token by username code.",
    )
    @atomic
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = SlidingTokenObtainByUsernameCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = TokenGeneratorByCode(**serializer.validated_data)()
        return Response({"token": str(token)}, status=HTTP_200_OK)


class TokenObtainByPasswordView(jwt.TokenObtainSlidingView):
    throttle_classes = [AuthAnonRateThrottle]


class TokenRefreshView(jwt.TokenRefreshSlidingView):
    throttle_classes = [AuthAnonRateThrottle]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore
        serializer = self.get_serializer(data=request.data)

        try:
            user_id = serializer.token_class(request.data["token"])["user_id"]  # type: ignore
            serializer.is_valid(raise_exception=True)
        except (TokenError, KeyError) as e:
            raise InvalidToken(e.args[0])

        user = User.objects.get(pk=user_id)
        if not user.is_active:
            raise InvalidToken("Inactive user")

        return Response(serializer.validated_data, status=HTTP_200_OK)


class TokenByUserId(APIView):
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        responses={"200": ResponseSlidingTokenObtainByUsernameCodeSerializer},
        description="Obtain token by user id.",
    )
    def get(self, request: Request, user_id: int) -> Response:
        user = get_object_or_404(User, pk=user_id)
        if not user.is_active:
            return Response(status=400, data={"serviceError": _("Inactive user")})
        return Response({"token": str(SlidingToken.for_user(user))}, status=HTTP_200_OK)


class TokenBySocialView(SocialJWTSlidingOnlyAuthView):
    """
    View will login the user from social oauth2.0 provider.

    **Input** (default serializer_class_in):

        {
            "provider": "yaru",  # options: mailru, yaru, google-oauth2, apple-id
            "code": "AQBPBBTjbdnehj51"
        }

    + optional

        "redirect_uri": "/relative/or/absolute/redirect/uri"

    **Output**:

    user data in serializer_class format
    """

    serializer_class = SocialJWTSlidingSerializer
