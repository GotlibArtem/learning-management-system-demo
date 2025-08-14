from datetime import timedelta

from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel


class RecurrentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    CANCELLED = "CANCELLED", _("Cancelled")


class RecurrentChargeStatus(models.TextChoices):
    SUCCESS = "SUCCESS", _("Success")
    FAIL = "FAIL", _("Fail")


class Recurrent(TimestampedModel):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        verbose_name=_("User"),
        db_index=True,
        related_name="recurrent_subscriptions",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        verbose_name=_("Product"),
        related_name="recurrent_subscriptions",
        db_index=True,
        help_text=_("Product for which the recurring subscription is enabled."),
    )
    payment_instrument = models.ForeignKey(
        "payments.PaymentInstrument",
        on_delete=models.SET_NULL,
        verbose_name=_("Payment instrument"),
        related_name="recurrent_subscriptions",
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Payment instrument used for recurring charges."),
    )
    status = models.CharField(
        _("Status"),
        max_length=16,
        choices=RecurrentStatus.choices,
        default=RecurrentStatus.ACTIVE,
        db_index=True,
    )
    amount = models.DecimalField(
        _("Recurring charge amount"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Planned recurring charge amount."),
    )
    next_charge_date = models.DateTimeField(
        _("Next charge date"),
        db_index=True,
        null=True,
        blank=True,
        help_text=_("Planned date for next recurring charge."),
    )
    last_attempt_charge_date = models.DateTimeField(
        _("Last attempt charge date"),
        null=True,
        blank=True,
    )
    last_attempt_charge_status = models.CharField(
        _("Last attempt charge status"),
        max_length=8,
        choices=RecurrentChargeStatus.choices,
        default="",
        blank=True,
        db_index=True,
    )

    class Meta:
        verbose_name = _("Recurrent payment")
        verbose_name_plural = _("Recurrent payments")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["user", "product", "status"]),
        ]
        permissions = [
            ("allow_recurrent_integration", _("Can send requests for recurrent integration")),
        ]

    def __str__(self) -> str:
        return f"{self.user} — [{self.status}]"

    def is_active(self) -> bool:
        """Check if the recurrent subscription is active."""

        return self.status == RecurrentStatus.ACTIVE

    def update_next_charge_date(self, commit: bool = True) -> None:
        """Updates next_charge_date based on the product's lifetime."""

        base_date = self.last_attempt_charge_date or now()

        if not self.product or not hasattr(self.product, "lifetime"):
            raise ValueError("Product or its lifetime is missing.")

        self.next_charge_date = base_date + timedelta(days=self.product.lifetime)  # type: ignore[arg-type]
        if commit:
            self.save(update_fields=["next_charge_date"])

    def deactivate(self, commit: bool = True) -> None:
        """Deactivates the recurrent subscription."""

        self.status = RecurrentStatus.CANCELLED
        if commit:
            self.save(update_fields=["status"])
