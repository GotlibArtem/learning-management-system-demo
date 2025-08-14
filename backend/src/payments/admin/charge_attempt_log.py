from django.contrib import admin
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from app.admin import ModelAdmin
from payments.models import ChargeAttemptLog


MAX_ERROR_MSG_LENGTH = 100


@admin.register(ChargeAttemptLog)
class ChargeAttemptLogAdmin(ModelAdmin):
    list_display = [
        "user",
        "provider",
        "external_payment_id",
        "short_error_message",
        "created",
        "provider_response",
    ]
    list_select_related = [
        "user",
    ]
    search_fields = [
        "user__username",
        "provider",
        "external_payment_id",
    ]
    list_filter = [
        "provider",
    ]
    autocomplete_fields = [
        "user",
    ]
    readonly_fields = [
        "user",
        "provider",
        "external_payment_id",
        "provider_response",
        "error_message",
        "traceback",
        "created",
        "modified",
    ]
    ordering = ["-created"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: ChargeAttemptLog | None = None) -> bool:
        return False

    @admin.display(description=_("Error message"))
    def short_error_message(self, obj: ChargeAttemptLog) -> str:
        return obj.error_message[:MAX_ERROR_MSG_LENGTH] + "…" if len(obj.error_message) > MAX_ERROR_MSG_LENGTH else obj.error_message
