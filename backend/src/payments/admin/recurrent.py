from django.contrib.admin import register
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from nested_admin import NestedTabularInline

from app.admin import ModelAdmin
from payments.models import Payment, Recurrent, RecurrentChargeAttempt


class PaymentInline(NestedTabularInline):
    model = Payment
    fields = (
        "external_payment_id",
        "order_id",
        "provider",
        "amount",
        "status",
        "paid_at",
    )
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True
    ordering = ("-paid_at",)

    def has_add_permission(self, request: HttpRequest, obj: Payment | None = None) -> bool:
        return False


class RecurrentChargeAttemptInline(NestedTabularInline):
    model = RecurrentChargeAttempt
    fields = (
        "status",
        "amount",
        "payment",
        "created",
        "error_code",
        "error_message",
    )
    readonly_fields = fields
    extra = 0
    show_change_link = True
    ordering = ("-created",)

    def has_add_permission(self, request: HttpRequest, obj: RecurrentChargeAttempt | None = None) -> bool:
        return False


@register(Recurrent)
class RecurrentAdmin(ModelAdmin):
    list_display = (
        "id",
        "user",
        "product",
        "payment_instrument",
        "status",
        "amount",
        "next_charge_date",
        "last_attempt_charge_date",
        "last_attempt_charge_status",
    )
    search_fields = ("user__username", "product__name")
    list_filter = ("status", "payment_instrument__provider", "payment_instrument__payment_method")
    autocomplete_fields = ("user", "product", "payment_instrument")
    readonly_fields = (
        "id",
        "user",
        "product",
        "created",
        "modified",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "user",
                    "product",
                ),
            },
        ),
        (
            _("Payment information"),
            {
                "fields": (
                    "payment_instrument",
                    "status",
                    "amount",
                    "next_charge_date",
                    "last_attempt_charge_date",
                    "last_attempt_charge_status",
                ),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ["created", "modified"],
            },
        ),
    )
    inlines = [PaymentInline, RecurrentChargeAttemptInline]
    ordering = ("-created",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
