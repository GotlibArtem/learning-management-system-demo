from django.db import models
from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel
from users.models import User


class ProductAccessQuerySet(QuerySet):
    def active_for_user(self, user: User) -> "ProductAccessQuerySet":
        today = timezone.now().date()
        return self.filter(
            Q(user=user),
            Q(start_date__date__lte=today),
            Q(end_date__date__gte=today) | Q(end_date__isnull=True),
            Q(revoked_at__isnull=True),
        )

    def all_subscriptions_for_user(self, user: User) -> "ProductAccessQuerySet":
        return self.filter(
            user=user,
            product__product_type="subscription",
            revoked_at__isnull=True,
        )


class ProductAccess(TimestampedModel):
    objects = ProductAccessQuerySet.as_manager()

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        verbose_name=_("Product"),
        related_name="access_items",
        null=True,  # may be null in the case of product revoke events for nonexistent access
        blank=True,
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        related_name="product_access_items",
        null=True,  # may be null in the case of product revoke events for nonexistent access
        blank=True,
    )
    start_date = models.DateTimeField(
        verbose_name=_("Start date"),
        db_index=True,
    )
    end_date = models.DateTimeField(
        _("End date"),
        null=True,
        blank=True,
        db_index=True,
    )
    order_id = models.CharField(
        _("Order ID"),
        max_length=128,
        db_index=True,
        unique=True,
    )
    granted_at = models.DateTimeField(
        _("Granted at"),
        db_index=True,
        null=True,
        blank=True,
    )
    revoked_at = models.DateTimeField(
        _("Revoked at"),
        db_index=True,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Product access")
        verbose_name_plural = _("Product access")
        ordering = ["created"]
        unique_together = [("product", "user", "start_date", "end_date")]
        indexes = [
            models.Index(fields=["revoked_at", "start_date", "end_date"]),
            models.Index(fields=["revoked_at", "start_date", "end_date", "user"]),
            models.Index(fields=["revoked_at", "start_date", "end_date", "user", "product"]),
            models.Index(fields=["user", "start_date", "end_date", "revoked_at"]),
            models.Index(fields=["product", "user", "start_date", "end_date", "revoked_at"]),
        ]
        permissions = [
            ("allow_shop_integration", _("Can send integration requests from the shop")),
        ]
