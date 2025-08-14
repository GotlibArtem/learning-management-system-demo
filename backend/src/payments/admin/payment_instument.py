from django.contrib.admin import register
from django.http import HttpRequest
from nested_admin import NestedTabularInline

from app.admin import ModelAdmin
from payments.models import Payment, PaymentInstrument, Recurrent


class PaymentInline(NestedTabularInline):
    model = Payment
    fields = (
        "external_payment_id",
        "order_id",
        "product",
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

    def has_delete_permission(self, request: HttpRequest, obj: Payment | None = None) -> bool:
        return False


class InstrumentRecurrentInline(NestedTabularInline):
    model = Recurrent
    fields = (
        "product",
        "status",
        "amount",
        "next_charge_date",
        "last_attempt_charge_status",
    )
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True
    ordering = ("-created",)

    def has_add_permission(self, request: HttpRequest, obj: Recurrent | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Recurrent | None = None) -> bool:
        return False


@register(PaymentInstrument)
class PaymentInstrumentAdmin(ModelAdmin):
    list_display = (
        "user",
        "provider",
        "payment_method",
        "card_mask",
        "exp_date",
        "rebill_id",
        "status",
    )
    search_fields = ("user__username", "card_mask", "rebill_id")
    list_filter = ("provider", "payment_method", "status")
    autocomplete_fields = ("user",)
    readonly_fields = (
        "user",
        "provider",
        "payment_method",
        "card_mask",
        "exp_date",
        "card_id",
        "rebill_id",
        "token",
        "created",
        "modified",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "provider",
                    "payment_method",
                    "card_mask",
                    "exp_date",
                    "card_id",
                    "rebill_id",
                    "status",
                    "token",
                    "created",
                    "modified",
                ),
            },
        ),
    )
    inlines = [InstrumentRecurrentInline, PaymentInline]
    ordering = ("-created",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
