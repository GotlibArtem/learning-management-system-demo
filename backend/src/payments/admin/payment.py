from django.contrib.admin import register
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from app.admin import ModelAdmin
from payments.models import Payment


@register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = (
        "id",
        "external_payment_id",
        "order_id",
        "user",
        "product",
        "provider",
        "payment_method",
        "amount",
        "status",
        "paid_at",
        "is_recurrent",
    )
    list_filter = (
        "provider",
        "payment_method",
        "status",
        "source",
        "is_recurrent",
    )
    search_fields = (
        "id",
        "external_payment_id",
        "order_id",
        "user__username",
        "product__name",
        "amount",
    )
    autocomplete_fields = ("user", "product", "recurrent")
    readonly_fields = (
        "id",
        "external_payment_id",
        "order_id",
        "user",
        "product",
        "provider",
        "payment_method",
        "paid_at",
        "payment_instrument",
        "is_recurrent",
        "recurrent",
        "order_price",
        "discount_price",
        "total_price",
        "amount",
        "bonus_applied",
        "provider_response",
        "created",
        "modified",
    )
    fieldsets = (
        (
            None,
            {
                "fields": ["id", "user", "product", "external_payment_id", "order_id", "amount", "status", "paid_at"],
            },
        ),
        (
            _("Payment information"),
            {
                "fields": [
                    "source",
                    "provider",
                    "payment_method",
                    "payment_instrument",
                    "is_recurrent",
                    "recurrent",
                    "order_price",
                    "discount_price",
                    "total_price",
                    "bonus_applied",
                    "promo_code",
                ],
            },
        ),
        (
            _("Payment details"),
            {
                "fields": [
                    "provider_response",
                ],
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ["created", "modified"],
            },
        ),
    )

    ordering = ("-paid_at",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
