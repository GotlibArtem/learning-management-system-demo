from dataclasses import dataclass

from django.utils.translation import gettext as _

from app.exceptions import AppServiceException
from app.services import BaseService
from bonuses.models import BonusAccount
from users.models import User


class BonusAccountGetterException(AppServiceException):
    """Exception for bonus account getter errors."""


@dataclass
class BonusAccountGetter(BaseService):
    email: str

    def act(self) -> BonusAccount:
        account, _created = BonusAccount.objects.get_or_create(user=self.get_user())
        if account.is_active is False:
            raise BonusAccountGetterException(_("Bonus account is not active."))

        return account

    def get_user(self) -> User:
        try:
            user = User.objects.get(username=self.email)
        except User.DoesNotExist:
            raise BonusAccountGetterException(_("User matching query does not exist."))

        return user
