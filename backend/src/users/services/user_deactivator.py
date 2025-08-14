from dataclasses import dataclass

from django.db.transaction import atomic
from django.utils.translation import gettext as _

from app.exceptions import AppServiceException
from app.services import BaseService
from users.models import User


class UserDeactivatorException(AppServiceException):
    """
    Raise for any user deactivating error
    """


@dataclass
class UserDeactivator(BaseService):
    """
    Deactivate user
    """

    user: User

    @atomic
    def act(self) -> None:
        if not self.user.is_active:
            raise UserDeactivatorException(_("User is already deactivated"))

        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
