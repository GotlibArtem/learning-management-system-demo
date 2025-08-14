from dataclasses import dataclass

from django.utils import timezone

from app.services import BaseService
from users.models import User


@dataclass
class UserEmailConfirmator(BaseService):
    """
    Saves user email confirmation date.
    """

    user: User

    def act(self) -> None:
        if self.user.email_confirmed_at is not None:
            return

        self.user.email_confirmed_at = timezone.now()
        self.user.save(update_fields=["email_confirmed_at"])
