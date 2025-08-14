from typing import Any

from django.contrib.admin import TabularInline, register
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from app.admin import ModelAdmin
from bonuses.models import BonusAccount, BonusTransaction


class BonusTransactionInline(TabularInline):
    model = BonusTransaction
    extra = 0
    can_delete = False
    show_change_link = False
    ordering = ["-created"]

    fields = ["amount", "transaction_type", "reason", "created_by", "created"]
    readonly_fields = ["amount", "transaction_type", "reason", "created_by", "created", "modified"]

    def has_add_permission(self, request, obj=None) -> bool:  # type: ignore
        return False


@register(BonusAccount)
class BonusAccountAdmin(ModelAdmin):
    list_display = ["user", "balance", "is_active", "created", "modified"]
    list_filter = ["is_active", "created", "modified"]

    list_editable = ["is_active"]

    search_fields = [
        "user__email",
        "user__username",
        "user__id",
    ]
    readonly_fields = ["user", "balance", "created", "modified"]
    ordering = ["-created"]

    def get_model_perms(self, request: Any) -> dict:
        return {}

    inlines = [BonusTransactionInline]

    fieldsets = [
        (
            None,
            {
                "fields": ["user", "balance", "is_active"],
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ["created", "modified"],
            },
        ),
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return True

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False
