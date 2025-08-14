from django.db import models
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel
from payments.models import PaymentMethod, PaymentProvider


class PaymentInstrumentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")
    REVOKED = "REVOKED", _("Revoked")
    EXPIRED = "EXPIRED", _("Expired")


class PaymentInstrument(TimestampedModel):
    """Stores a linked payment method for recurring or one-click payments."""

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        related_name="payment_instruments",
        db_index=True,
        help_text=_("User who owns this payment instrument."),
    )
    provider = models.CharField(
        _("Provider"),
        max_length=16,
        choices=PaymentProvider.choices,
        db_index=True,
        help_text=_("Payment provider (Tinkoff, Stripe, etc.)."),
    )
    payment_method = models.CharField(
        _("Payment method"),
        max_length=24,
        choices=PaymentMethod.choices,
        db_index=True,
        help_text=_("Method used for payment (card, sbp, apple pay, etc.)."),
    )
    card_mask = models.CharField(
        _("Card mask"),
        max_length=24,
        blank=True,
        default="",
        help_text=_("Masked card number (e.g. ****7382)."),
    )
    exp_date = models.CharField(
        _("Expiry date"),
        max_length=6,
        blank=True,
        default="",
        help_text=_("Card expiration date in MMYY format (e.g. 0925)."),
    )
    card_id = models.CharField(
        _("Card ID"),
        max_length=64,
        blank=True,
        default="",
        help_text=_("Optional card ID from provider (used for some providers)."),
    )
    rebill_id = models.CharField(
        _("Rebill ID"),
        max_length=64,
        db_index=True,
        blank=True,
        default="",
        help_text=_("Rebill ID used to initiate recurring charges."),
    )
    status = models.CharField(
        _("Status"),
        max_length=16,
        choices=PaymentInstrumentStatus.choices,
        default=PaymentInstrumentStatus.ACTIVE,
        db_index=True,
        help_text=_("Current status of the payment instrument."),
    )
    token = models.CharField(
        _("Card token"),
        max_length=512,
        blank=True,
        default="",
        help_text=_("Optional provider token (not used for payment, but may be useful for unsubscribing, deleting or managing the card)."),
    )

    class Meta:
        verbose_name = _("Payment instrument")
        verbose_name_plural = _("Payment instruments")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["user", "provider", "rebill_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.card_mask} — {self.provider}"
