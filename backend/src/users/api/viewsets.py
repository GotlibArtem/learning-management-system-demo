from django.contrib.auth import logout
from django.db.models import QuerySet
from django.db.transaction import on_commit
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import SlidingToken

from a12n.models import PasswordlessEmailAuthCode
from app.api.request import AuthenticatedRequest
from app.api.viewsets import RetrieveOrUpdateModelViewSet
from app.services import PlatformDetector
from mindbox.tasks import send_customer_interests
from users.api.serializers import (
    ResponseSocialUserSignUpSerializer,
    SocialUserSignUpSerializer,
    UserBonusesSerializer,
    UserCommentTokenSerializer,
    UserInterestsSerializer,
    UserRecurrentInfoSerializer,
    UserSerializer,
    UserSignInSerializer,
    UserSignUpSerializer,
    UserUpdateSerializer,
)
from users.api.throttling import SignUpAnonRateThrottle
from users.models import User
from users.services import (
    OAuthUserFetcher,
    UserAllInterestsUpdater,
    UserBonusesGetter,
    UserCommentTokenGetter,
    UserDeactivator,
    UserEditor,
    UserInterestsSetter,
    UserRecurrentCanceller,
    UserRecurrentInfoGetter,
    UserSignerUp,
)
from users.tasks import send_user_auth_code_to_email


class SelfView(RetrieveOrUpdateModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    serializer_action_classes = {
        "partial_update": UserUpdateSerializer,
    }
    request: AuthenticatedRequest

    @extend_schema(
        description="Get user bonuses count",
        responses=UserBonusesSerializer,
    )
    @action(detail=True, methods=["get"])
    def bonuses(self, request: AuthenticatedRequest) -> Response:
        bonuses_count = UserBonusesGetter(user=request.user)()
        return Response(UserBonusesSerializer({"bonuses": bonuses_count}).data)

    @extend_schema(
        description="Get user cackle auth key",
        responses=UserCommentTokenSerializer,
    )
    @action(detail=True, methods=["get"])
    def comment_auth(self, request: AuthenticatedRequest) -> Response:
        comment_auth = UserCommentTokenGetter(user=request.user)()
        return Response(UserCommentTokenSerializer(comment_auth).data)

    @extend_schema(
        description="Deactivate account and log out user",
        request=None,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=False, methods=["post"])
    def deactivate(self, request: AuthenticatedRequest) -> Response:
        UserDeactivator(user=request.user)()
        self.perform_logout(request)
        return Response(status=HTTP_204_NO_CONTENT)

    def get(self, request: Request) -> Response:
        user = self.get_object()
        serializer = self.get_serializer(user)

        return Response(serializer.data)

    def perform_update(self, serializer: BaseSerializer) -> User:  # type: ignore[override]
        user = self.get_object()
        return UserEditor(username=user.username, **serializer.validated_data.copy())()[0]

    def get_object(self) -> User:
        return self.get_queryset().get(pk=self.request.user.pk)

    def get_queryset(self) -> QuerySet[User]:
        return User.objects.filter(is_active=True)

    def perform_logout(self, request: AuthenticatedRequest) -> None:
        logout(request)


class SignUpView(APIView):
    serializer_class = UserSignUpSerializer
    permission_classes = [AllowAny]
    throttle_classes = [SignUpAnonRateThrottle]

    @extend_schema(
        request=UserSignUpSerializer,
        responses=UserSerializer,
        description="User sign up.",
    )
    def post(self, request: Request) -> Response:
        serializer = UserSignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sign_up_data = dict(serializer.validated_data)

        user = UserSignerUp(**sign_up_data)()
        auth_code = PasswordlessEmailAuthCode.objects.create(user=user)

        send_user_auth_code_to_email.delay(str(auth_code.id))

        return Response(UserSerializer(user, context={"request": request}).data, status=HTTP_201_CREATED)


class SignInView(APIView):
    serializer_class = UserSignInSerializer
    permission_classes = [AllowAny]
    throttle_classes = [SignUpAnonRateThrottle]

    @extend_schema(
        request=UserSignInSerializer,
        responses=UserSignInSerializer,
        description="User sign in.",
    )
    def post(self, request: Request) -> Response:
        serializer = UserSignInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sign_in_data = dict(serializer.validated_data)

        # Please, move it to service object
        user = User.objects.filter(username__iexact=sign_in_data["username"]).first()
        if not user:
            if PlatformDetector(request).is_ios:
                return Response(status=400, data={"serviceError": _("Account does not exist, try another one.")})

            return Response(status=400, data={"serviceError": _("Account does not exist, try another one or create a new one.")})

        if not user.is_apple_review_account():
            auth_code = PasswordlessEmailAuthCode.objects.create(user=user)
            send_user_auth_code_to_email.delay(str(auth_code.id))

        return Response({"username": user.username}, status=HTTP_200_OK)


class SocialSignUpView(APIView):
    serializer_class = SocialUserSignUpSerializer
    permission_classes = [AllowAny]
    throttle_classes = [SignUpAnonRateThrottle]

    @extend_schema(
        request=SocialUserSignUpSerializer,
        responses={"200": ResponseSocialUserSignUpSerializer},
        description="User sign up via social provider.",
    )
    def post(self, request: Request) -> Response:
        serializer = SocialUserSignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sign_up_data = dict(serializer.validated_data)

        user_data = OAuthUserFetcher(**sign_up_data)()
        user = UserSignerUp(user_data["email"], user_data["first_name"], user_data["last_name"])()

        token = SlidingToken.for_user(user)

        return Response({"token": str(token)}, status=HTTP_200_OK)


class UserRecurrentInfoView(APIView):
    serializer_class = UserRecurrentInfoSerializer
    permission_classes = [IsAuthenticated]
    request: AuthenticatedRequest

    @extend_schema(
        responses=UserRecurrentInfoSerializer,
        description="Get information about the user's active recurrent subscription.",
    )
    def get(self, request: AuthenticatedRequest) -> Response:
        payload = UserRecurrentInfoGetter(user=request.user)()

        return Response(UserRecurrentInfoSerializer(payload).data, status=HTTP_200_OK)

    @extend_schema(
        request=None,
        responses={HTTP_204_NO_CONTENT: None},
        description="Unbind payment instrument and cancel user's recurrent subscription.",
    )
    def delete(self, request: AuthenticatedRequest) -> Response:
        UserRecurrentCanceller(user=request.user)()
        return Response(status=HTTP_204_NO_CONTENT)
