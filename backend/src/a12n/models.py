from datetime import datetime
from typing import Optional

from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel, models
from users.models import User


def gen_code() -> str:
    return get_random_string(length=settings.PASSWORDLESS_EMAIL_CODE_LENGTH, allowed_chars="0123456789")


def default_expiration() -> datetime:
    return timezone.now() + settings.PASSWORDLESS_EMAIL_CODE_EXPIRATION_TIME


class PasswordlessEmailAuthCodeQuerySet(models.QuerySet):
    def get_valid_code(self, user: User, code: str) -> Optional["PasswordlessEmailAuthCode"]:
        return self.filter(
            user=user,
            code=code,
            expires__gt=timezone.now(),
            used__isnull=True,
        ).first()


PasswordlessEmailAuthCodeManager = models.Manager.from_queryset(PasswordlessEmailAuthCodeQuerySet)


class PasswordlessEmailAuthCode(TimestampedModel):
    objects = PasswordlessEmailAuthCodeManager()

    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    code = models.CharField(default=gen_code, db_index=True, max_length=100)
    expires = models.DateTimeField(default=default_expiration)
    used = models.DateTimeField(null=True)

    def mark_as_used(self) -> None:
        self.used = timezone.now()
        self.save(update_fields=["used", "modified"])

    class Meta:
        verbose_name = _("Passwordless email auth code")
        verbose_name_plural = _("Passwordless email auth codes")
