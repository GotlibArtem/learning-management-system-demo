from django.contrib.admin import register
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from app.admin import ModelAdmin
from payments.models import RecurrentChargeAttempt


@register(RecurrentChargeAttempt)
class RecurrentChargeAttemptAdmin(ModelAdmin):
    list_display = (
        "id",
        "recurrent",
        "status",
        "amount",
        "payment",
        "created",
    )
    search_fields = (
        "recurrent__id",
        "recurrent__user__username",
        "external_payment_id",
        "error_code",
    )
    list_filter = ("status",)
    autocomplete_fields = (
        "recurrent",
        "payment",
    )
    readonly_fields = (
        "id",
        "recurrent",
        "payment",
        "status",
        "amount",
        "error_code",
        "error_message",
        "external_payment_id",
        "provider_response",
        "created",
        "modified",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "recurrent",
                    "payment",
                    "status",
                    "amount",
                    "external_payment_id",
                    "provider_response",
                ),
            },
        ),
        (
            _("Error Details"),
            {
                "fields": (
                    "error_code",
                    "error_message",
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
    ordering = ("-created",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
