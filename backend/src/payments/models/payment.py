from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel


class PaymentMethod(models.TextChoices):
    CARD = "CARD", _("Bank card")
    CARD_RECURRENT = "CARD_RECURRENT", _("Bank card (recurrent)")
    SBP = "SBP", _("SBP (Fast Payments)")
    SBP_RECURRENT = "SBP_RECURRENT", _("SBP (Fast Payments, recurrent)")
    APPLE_PAY = "APPLE_PAY", _("Apple Pay")
    GOOGLE_PAY = "GOOGLE_PAY", _("Google Pay")


class PaymentProvider(models.TextChoices):
    DOLYAME = "DOLYAME", _("Dolyame")
    SPLIT = "SPLIT", _("Split")
    STRIPE = "STRIPE", _("Stripe")
    TINKOFF = "TINKOFF", _("Tinkoff")
    APPLE_PAY = "APPLE_PAY", _("Apple Pay")
    GOOGLE_PAY = "GOOGLE_PAY", _("Google Pay")


class PaymentSource(models.TextChoices):
    SITE = "SITE", _("Site (shop)")
    ADMIN = "ADMIN", _("Shop admin panel")
    LMS = "LMS", _("LMS (internal)")
    APPLE = "APPLE", _("Apple")
    GOOGLE = "GOOGLE", _("Google")
    RECURRING = "RECURRING", _("Recurring (auto-charge)")


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    PAID = "PAID", _("Paid")
    CANCELLED = "CANCELLED", _("Cancelled")
    REFUNDED = "REFUNDED", _("Refunded")
    FAILED = "FAILED", _("Failed")


class Payment(TimestampedModel):
    """
    Records all user payments (one-time and recurring).
    """

    external_payment_id = models.CharField(
        _("External payment ID"),
        max_length=128,
        db_index=True,
        unique=True,
        help_text=_("Payment ID in external payment system (or payment id from shop)."),
    )
    order_id = models.CharField(
        _("Order ID"),
        max_length=128,
        db_index=True,
        help_text=_("Unique identifier for the order associated with this payment in the shop system."),
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        verbose_name=_("User"),
        related_name="payments",
        db_index=True,
        null=True,
        blank=True,
        help_text=_("User who made this payment."),
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        verbose_name=_("Product"),
        related_name="payments",
        db_index=True,
        null=True,
        blank=True,
        help_text=_("Product purchased with this payment."),
    )
    payment_instrument = models.ForeignKey(
        "payments.PaymentInstrument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name=_("Payment instrument"),
        help_text=_("Instrument used for this payment (card, sbp, etc)."),
    )
    is_recurrent = models.BooleanField(
        _("Is recurrent"),
        default=False,
        db_index=True,
        help_text=_("True if this payment was initiated as recurring."),
    )
    recurrent = models.ForeignKey(
        "payments.Recurrent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name=_("Recurrent"),
        help_text=_("Linked recurrent subscription if this payment was made automatically."),
    )
    source = models.CharField(
        _("Source"),
        max_length=24,
        choices=PaymentSource.choices,
        default=PaymentSource.SITE,
        db_index=True,
        help_text=_("Source of payment creation (site, admin, lms, apple, google, recurring)."),
    )
    provider = models.CharField(
        _("Provider"),
        max_length=16,
        choices=PaymentProvider.choices,
        db_index=True,
        help_text=_("Payment provider (Tinkoff, Stripe, Dolyame, etc.)."),
    )
    payment_method = models.CharField(
        _("Payment method"),
        max_length=24,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CARD,
        db_index=True,
        help_text=_("How user paid (card, Apple Pay, etc.)."),
    )
    status = models.CharField(
        _("Status"),
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
        help_text=_("Current status of the payment."),
    )
    paid_at = models.DateTimeField(
        _("Paid at"),
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Datetime when payment was successfully processed."),
    )
    order_price = models.DecimalField(
        _("Order price"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Original order price before discounts and bonuses."),
    )
    discount_price = models.DecimalField(
        _("Discount price"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Total discount price applied (can be calculated: order_price - total_price)."),
    )
    total_price = models.DecimalField(
        _("Total price"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Total price after all discounts, bonuses, promo codes (should be the amount to pay)."),
    )
    amount = models.DecimalField(
        _("Amount paid"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Amount actually paid by the user (after all adjustments)."),
    )
    bonus_applied = models.DecimalField(
        _("Bonuses applied"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Bonuses applied to the payment, if any."),
    )
    promo_code = models.CharField(
        _("Promo code"),
        max_length=64,
        default="",
        blank=True,
        help_text=_("Applied promo code, if any."),
    )
    provider_response = models.JSONField(
        _("Provider response"),
        null=True,
        blank=True,
        help_text=_("Raw response from payment provider."),
    )

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["user", "product", "status"]),
            models.Index(fields=["external_payment_id"]),
            models.Index(fields=["is_recurrent"]),
            models.Index(fields=["provider", "status"]),
        ]
        permissions = [
            ("allow_payment_integration", _("Can send requests for payment integration")),
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.product} — {self.amount} ([{self.status}])"

    @property
    def is_successful(self) -> bool:
        return self.status == PaymentStatus.PAID

    @property
    def is_refunded(self) -> bool:
        return self.status == PaymentStatus.REFUNDED
