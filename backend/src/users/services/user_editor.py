from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any, ClassVar

from django.db import IntegrityError, transaction
from django.db.transaction import on_commit
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from app.exceptions import AppServiceException
from app.services import BaseService
from mindbox.tasks import edit_customer
from users.models import User
from users.services.user_creator import UserCreator


class UserEditorException(AppServiceException):
    """
    Raise for any user editing error
    """


@dataclass
class UserEditor(BaseService):
    """
    Create or update user by email
    """

    empty_value: ClassVar = str

    username: str
    phone: str | None = empty_value
    first_name: str | None = empty_value
    last_name: str | None = empty_value
    birthdate: date | None = empty_value
    avatar_slug: str | None = empty_value
    rhash: str | None = empty_value
    has_accepted_data_consent: bool | None = empty_value

    def __post_init__(self) -> None:
        self.phone = self.phone or ""
        self.first_name = self.first_name or ""
        self.last_name = self.last_name or ""
        self.avatar_slug = self.avatar_slug or ""
        self.rhash = self.rhash or ""
        self.has_accepted_data_consent = self.has_accepted_data_consent or False

    def act(self) -> tuple[User, bool]:
        user = self.get_user()
        if user is None:
            try:
                return (
                    UserCreator(username=self.username, **self.user_kwargs)(),
                    True,
                )
            except IntegrityError:
                # rollback the failed transaction to allow a new atomic block
                transaction.set_rollback(True)

                # Retry getting the user in a clean transaction
                with transaction.atomic():
                    user = self.get_user()
                    if user is None:
                        raise

        on_commit(lambda: edit_customer.delay(str(user.id)))
        return self.update_user(user), False

    def get_user(self) -> User | None:
        try:
            return User.objects.get(username=self.normalized_username)
        except User.DoesNotExist:
            return None

    def update_user(self, user: User) -> User:
        user.update_from_kwargs(**self.user_kwargs)
        user.save(update_fields=self.user_kwargs.keys())

        return user

    @property
    def user_kwargs(self) -> dict[str, Any]:
        kwargs = {
            "phone": self.normalized_phone if self.phone is not self.empty_value else self.phone,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "birthdate": self.birthdate,
            "avatar_slug": self.avatar_slug,
            "rhash": self.rhash,
            "has_accepted_data_consent": self.has_accepted_data_consent,
        }
        return {field: value for field, value in kwargs.items() if value is not self.empty_value}

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

    def get_validators(self) -> list[Callable]:
        return [
            self.validate_birthdate,
        ]

    def validate_birthdate(self) -> None:
        if self.birthdate == self.empty_value or self.birthdate is None:
            return None

        if timezone.now().date() < self.birthdate:
            raise UserEditorException(_("We can't believe you haven't been born yet"))
