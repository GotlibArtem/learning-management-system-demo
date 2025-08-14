from django.contrib import admin, messages
from django.contrib.admin import register
from django.db.models import QuerySet
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _

from app.admin.model_admin import ModelAdmin
from app.models import ShopDeadLetter
from product_access.api.demo.serializers import OrderCheckoutSerializer
from product_access.services import ProductCheckoutProcessor


__all__ = [
    "ModelAdmin",
    "admin",
]

admin.site.site_header = _("Demo LMS Admin")
admin.site.site_title = _("Demo LMS Admin")
admin.site.index_title = _("Demo LMS Admin")


@register(ShopDeadLetter)
class ShopDeadLetterAdmin(ModelAdmin):
    list_display = [
        "event_type",
        "created",
    ]

    list_filter = [
        "event_type",
        "created",
    ]

    search_fields = [
        "=event_type",
        "raw_data",
        "details",
    ]
    actions = [
        "resend_grant_access_event",
    ]

    @admin.action(description=_("Resend grant access events"))
    def resend_grant_access_event(self, request: HttpRequest, queryset: QuerySet[ShopDeadLetter]) -> None:
        for dead_letter in queryset:
            serializer = OrderCheckoutSerializer(data=dead_letter.raw_data)
            serializer.is_valid(raise_exception=True)
            ProductCheckoutProcessor(checkout_event=serializer.validated_data.copy())()

        self.message_user(
            request,
            _("Events are resent").format(count=queryset.count()),
            messages.SUCCESS,
        )
