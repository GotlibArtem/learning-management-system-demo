from collections.abc import Callable
from dataclasses import dataclass

from django.db.transaction import on_commit
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import SlidingToken, Token

from a12n.models import PasswordlessEmailAuthCode
from app.exceptions import AppServiceException
from app.services import BaseService
from mindbox.tasks import notify_user_logged_in
from users.models import User
from users.services import UserEmailConfirmator


class TokenGeneratorByCodeException(AppServiceException):
    """Raised when credentials are invalid."""


@dataclass
class TokenGeneratorByCode(BaseService):
    """Service for generating authentication token by username and code."""

    username: str
    code: str
    device_uuid: str

    def act(self) -> Token:
        if self.device_uuid:
            on_commit(lambda: notify_user_logged_in.delay(str(self.user.id), self.device_uuid))
        UserEmailConfirmator(self.user)()
        return SlidingToken.for_user(self.user)

    @cached_property
    def user(self) -> User:
        user = User.objects.filter(username__iexact=self.username).first()
        if not user:
            raise TokenGeneratorByCodeException(_("Account does not exist, try another one or create a new one."))
        return user

    def get_validators(self) -> list[Callable]:
        return [
            self.validate_user,
            self.validate_code,
        ]

    def validate_user(self) -> None:
        if not self.user.is_active:
            raise TokenGeneratorByCodeException(_("Inactive user, please, contact the administrator."))

    def validate_code(self) -> None:
        auth_code = PasswordlessEmailAuthCode.objects.get_valid_code(self.user, self.code)
        if not auth_code:
            raise TokenGeneratorByCodeException(_("Invalid code, please try again."))
        if not self.user.is_apple_review_account():
            auth_code.mark_as_used()
