from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property

from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _

from app.exceptions import AppServiceException
from app.services import BaseService
from users.models import User
from users.services import UserEditor


class UserSignerUpException(AppServiceException):
    """Raise if it is impossible to register user."""


@dataclass
class UserSignerUp(BaseService):
    username: str
    first_name: str | None = None
    last_name: str | None = None

    @atomic
    def act(self) -> User:
        return UserEditor(username=self.username, first_name=self.first_name, last_name=self.last_name)()[0]

    def validate_if_user_already_registered(self) -> None:
        if not self.existent_user:
            return

        if self.existent_user.email_confirmed_at is not None:
            raise UserSignerUpException(_("User already registered."))

    @cached_property
    def existent_user(self) -> User | None:
        return User.objects.filter(username=self.username).first()

    def get_validators(self) -> list[Callable]:
        return [
            self.validate_if_user_already_registered,
        ]
