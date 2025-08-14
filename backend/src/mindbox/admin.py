from typing import Any

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from mindbox.models import CorporateEmailDomain, MindboxOperationLog


@admin.register(CorporateEmailDomain)
class CorporateEmailDomainAdmin(admin.ModelAdmin):
    list_display = ["domain", "created", "modified"]
    search_fields = ["domain"]
    ordering = ["domain"]
    readonly_fields = ["id", "created", "modified"]

    fieldsets = (
        (None, {"fields": ("id",)}),
        (_("Domain info"), {"fields": ("domain",)}),
        (_("Timestamps"), {"fields": ("created", "modified")}),
    )


@admin.register(MindboxOperationLog)
class MindboxOperationLogAdmin(admin.ModelAdmin):
    fields = ["operation", "destination", "content"]
    list_display = ["operation", "destination", "created"]
    list_filter = ["operation"]
    ordering = ["-created"]

    def has_add_permission(self, *args: Any, **kwargs: Any) -> bool:  # type: ignore
        return False

    def has_change_permission(self, *args: Any, **kwargs: Any) -> bool:  # type: ignore
        return False
