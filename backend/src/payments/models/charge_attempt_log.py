from django.db import models
from django.utils.translation import gettext_lazy as _

from app.json_encoders import AppJSONEncoder
from app.models import TimestampedModel
from payments.models.payment import PaymentProvider


class ChargeAttemptLog(TimestampedModel):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("User"),
        related_name="charge_attempt_logs",
    )
    external_payment_id = models.CharField(
        verbose_name=_("External payment ID"),
        max_length=128,
        default="",
        blank=True,
        help_text=_("Payment ID in external payment system (or payment id from shop)."),
    )
    provider = models.CharField(
        _("Provider"),
        max_length=16,
        choices=PaymentProvider.choices,
        default="",
        blank=True,
        help_text=_("Payment provider (Tinkoff, Stripe, Dolyame, etc.)."),
    )
    provider_response = models.JSONField(
        _("Provider response"),
        null=True,
        blank=True,
        encoder=AppJSONEncoder,
        help_text=_("Raw response from payment provider."),
    )
    error_message = models.TextField(verbose_name=_("Error message"))
    traceback = models.TextField(
        verbose_name=_("Traceback"),
        blank=True,
    )

    class Meta:
        verbose_name = _("Charge Attempt Error Log")
        verbose_name_plural = _("Charge Attempt Error Logs")
        ordering = ["-created"]
