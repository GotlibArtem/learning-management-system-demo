from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.functional import cached_property

from app.exceptions import AppServiceException
from app.services import BaseService
from users.models import User


class UserImporterException(AppServiceException):
    """Raise on any import error"""


@dataclass
class UserImporter(BaseService):
    data: dict
    skip_if_user_exists: bool = False

    def act(self) -> User:
        if self.skip_if_user_exists and self.existent_user is not None:
            return self.existent_user

        return User.objects.update_or_create(
            username=self.username,
            defaults=dict(
                email=self.username,
                first_name=self.first_name,
                last_name=self.last_name,
                date_joined=self.date_joined,
                avatar_slug="abstract",
            ),
        )[0]

    @cached_property
    def existent_user(self) -> User | None:
        return User.objects.filter(username=self.username).first()

    def parse_date_joined(self, raw_value: str) -> datetime:
        return datetime.fromisoformat(raw_value)

    def get_validators(self) -> list[Callable]:
        return [
            self.validate_email,
        ]

    def validate_email(self) -> None:
        try:
            validate_email(self.username)
        except ValidationError:
            raise UserImporterException(f"invalid email {self.data['E-mail']}")

    @property
    def first_name(self) -> str:
        return self.data["Имя"].strip()

    @property
    def last_name(self) -> str:
        return self.data["Фамилия"].strip()

    @property
    def username(self) -> str:
        return self.data["E-mail"].strip().lower()

    @property
    def date_joined(self) -> datetime:
        return self.parse_date_joined(self.data["Дата регистрации"])
