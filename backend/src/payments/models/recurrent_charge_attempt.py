from django.db import models
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel
from payments.models import Payment, Recurrent, RecurrentChargeStatus


class RecurrentChargeAttempt(TimestampedModel):
    """Stores individual attempts to charge a user via a recurring payments."""

    recurrent = models.ForeignKey(
        Recurrent,
        on_delete=models.CASCADE,
        related_name="charge_attempts",
        verbose_name=_("Recurrent"),
        db_index=True,
        help_text=_("Recurring subscription for which this charge attempt was made."),
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="charge_attempts",
        verbose_name=_("Payment"),
        help_text=_("Linked payment if the charge was successful."),
    )
    status = models.CharField(
        _("Status"),
        max_length=8,
        choices=RecurrentChargeStatus.choices,
        db_index=True,
        help_text=_("Result of this charge attempt."),
    )
    amount = models.DecimalField(
        _("Attempted charge amount"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Amount attempted to be charged."),
    )
    currency = models.CharField(
        _("Currency"),
        max_length=8,
        blank=True,
        default="",
        help_text=_("Currency of the attempted charge."),
    )
    error_code = models.CharField(
        _("Error code"),
        max_length=64,
        blank=True,
        default="",
        help_text=_("Optional error code returned by the payment provider."),
    )
    error_message = models.TextField(
        _("Error message"),
        blank=True,
        default="",
        help_text=_("Detailed error message from provider, if any."),
    )
    external_payment_id = models.CharField(
        _("External payment ID"),
        max_length=128,
        blank=True,
        default="",
        help_text=_("ID of the payment in external system (if available)."),
    )
    provider_response = models.JSONField(
        _("Provider response"),
        null=True,
        blank=True,
        help_text=_("Raw response from the payment provider."),
    )

    class Meta:
        verbose_name = _("Recurrent charge attempt")
        verbose_name_plural = _("Recurrent charge attempts")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["recurrent", "status"]),
            models.Index(fields=["payment"]),
        ]

    def __str__(self) -> str:
        return f"{self.recurrent} — {self.status} — {self.created:%Y-%m-%d %H:%M}"
