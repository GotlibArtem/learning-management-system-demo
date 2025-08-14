from typing import Any

from django.contrib import admin

from a12n.models import PasswordlessEmailAuthCode


@admin.register(PasswordlessEmailAuthCode)
class PasswordlessEmailAuthCodeAdmin(admin.ModelAdmin):
    fields = ["user", "code", "expires", "used"]
    list_display = ["user", "code", "expires", "used"]
    readonly_fields = ["code", "expires", "used"]
    autocomplete_fields = ["user"]

    def has_change_permission(self, *args: Any, **kwargs: Any) -> bool:
        return False
