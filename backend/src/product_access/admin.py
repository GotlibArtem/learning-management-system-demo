from django.contrib.admin import EmptyFieldListFilter, register
from django.http import HttpRequest

from app.admin import ModelAdmin
from product_access.models import ProductAccess


@register(ProductAccess)
class ProductAccessAdmin(ModelAdmin):
    list_display = [
        "product",
        "user",
        "start_date",
        "end_date",
        "order_id",
        "created",
    ]
    list_select_related = [
        "product",
        "user",
    ]
    search_fields = [
        "product__name",
        "user__username",
        "=order_id",
    ]

    fields = [
        "user",
        "product",
        "start_date",
        "end_date",
        "order_id",
        "granted_at",
        "revoked_at",
    ]
    autocomplete_fields = [
        "user",
        "product",
    ]
    readonly_fields = [
        "user",
        "product",
        "start_date",
        "order_id",
        "granted_at",
        "revoked_at",
    ]
    list_filter = [
        ("revoked_at", EmptyFieldListFilter),
    ]
    ordering = ["-created"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: ProductAccess | None = None) -> bool:
        return obj is not None

    def delete_model(self, request: HttpRequest, obj: ProductAccess) -> None:
        if obj.user:
            from product_access.services import UserProductAccessCacheInvalidator

            UserProductAccessCacheInvalidator(user=obj.user)()
        super().delete_model(request, obj)
