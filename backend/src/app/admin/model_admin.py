from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME


class ModelAdmin(admin.ModelAdmin):
    """App-wide admin customizations"""

    export_action_names: list[str] = []

    def changelist_view(self, request, extra_context=None):  # type: ignore
        if request.method == "POST" and "action" in request.POST:
            action = request.POST["action"]

            if action in self.export_action_names and not request.POST.getlist(ACTION_CHECKBOX_NAME):
                queryset = self.get_queryset(request)
                return getattr(self, action)(request, queryset)

        return super().changelist_view(request, extra_context)
