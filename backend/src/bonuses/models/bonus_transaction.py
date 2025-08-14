from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel, models


class BonusTransactionType(models.TextChoices):
    EARNED = "earned", _("Earned")
    SPENT = "spent", _("Spent")
    ADMIN_EARNED = "admin_earned", _("Admin earned")
    ADMIN_SPENT = "admin_spent", _("Admin spent")


class BonusTransaction(TimestampedModel):
    account = models.ForeignKey(
        "bonuses.BonusAccount",
        on_delete=models.CASCADE,
        verbose_name=_("Bonus account"),
        related_name="transactions",
    )
    amount = models.IntegerField(
        verbose_name=_("Amount"),
        validators=[MinValueValidator(1)],
        help_text=_("Amount of bonuses (always positive)"),
    )
    transaction_type = models.CharField(
        verbose_name=_("Transaction type"),
        max_length=32,
        choices=BonusTransactionType.choices,
    )
    reason = models.CharField(
        verbose_name=_("Reason"),
        max_length=512,
        blank=True,
        help_text=_("Description of the transaction"),
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Created by"),
        related_name="bonus_transactions_created",
        help_text=_("User who created this transaction (for admin operations)"),
    )

    class Meta:
        ordering = ("-created",)
        verbose_name = _("Bonus transaction")
        verbose_name_plural = _("Bonus transactions")
        indexes = [
            models.Index(fields=["account", "-created"]),
            models.Index(fields=["transaction_type"]),
        ]
        permissions = [
            ("allow_bonuses_integration", _("Can send requests from the shop for user bonuses integration")),
        ]

    def __str__(self) -> str:
        return ""
