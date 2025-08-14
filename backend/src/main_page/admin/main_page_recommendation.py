from django.conf import settings
from django.contrib import admin
from rest_framework.request import Request

from main_page.models import MainPageRecommendation


@admin.register(MainPageRecommendation)
class MainPageRecommendationAdmin(admin.ModelAdmin):
    fields = ["id", "course", "position", "created", "modified"]
    list_display = ["course", "position"]

    list_editable = ["position"]

    autocomplete_fields = ["course"]
    readonly_fields = ["id", "created", "modified"]

    def has_add_permission(self, request: Request) -> bool:  # type: ignore
        if self.model.objects.count() >= settings.MAX_MAIN_PAGE_RECOMMENDATIONS:
            return False
        return super().has_add_permission(request)
