from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.transaction import atomic
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from app.exceptions import AppServiceException
from app.services import BaseService
from bonuses.models import BonusAccount
from users.models import User


class UserCreatorException(AppServiceException):
    """Raise if it is impossible to create user."""


@dataclass
class UserCreator(BaseService):
    username: str
    phone: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    birthdate: date | None = None
    avatar_slug: str | None = None
    rhash: str | None = None
    has_accepted_data_consent: bool | None = None

    @atomic
    def act(self) -> User:
        user = User(
            username=self.normalized_username,
            email=self.normalized_username,
            phone=self.normalized_phone or "",
            first_name=self.first_name or "",
            last_name=self.last_name or "",
            email_confirmed_at=None,
            birthdate=self.birthdate,
            avatar_slug=self.avatar_slug or "",
            rhash=self.rhash or "",
            has_accepted_data_consent=self.has_accepted_data_consent or None,
        )
        user.save()

        BonusAccount.objects.create(user=user)

        return user

    @cached_property
    def normalized_username(self) -> str:
        return self.username.strip().lower()

    @cached_property
    def normalized_phone(self) -> str:
        if not isinstance(self.phone, str):
            return ""
        phone = self.phone.strip()
        if not phone:
            return ""
        return phone if phone.startswith("+") else f"+{phone}"

    def validate_username(self) -> None:
        if not self.username:
            raise UserCreatorException(_("Email is required."))

        try:
            validate_email(self.normalized_username)
        except ValidationError:
            raise UserCreatorException(_("Invalid email."))

        if User.objects.filter(username=self.normalized_username).exists():
            raise UserCreatorException(_("User with such email already exists."))

    def get_validators(self) -> list[Callable]:
        return [
            self.validate_username,
        ]
