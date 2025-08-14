from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel


class BonusAccount(TimestampedModel):
    user = models.OneToOneField(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("User"),
        related_name="bonus_account",
    )
    balance = models.PositiveIntegerField(
        verbose_name=_("Balance"),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Current bonus balance"),
    )
    is_active = models.BooleanField(
        verbose_name=_("Is active"),
        default=True,
        help_text=_("Whether the bonus account is active"),
    )

    class Meta:
        ordering = ("-modified",)
        verbose_name = _("Bonus account")
        verbose_name_plural = _("Bonus accounts")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return ""
