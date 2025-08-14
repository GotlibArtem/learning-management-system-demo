from django.contrib import admin

from main_page.models import CourseBundleContent, CourseBundleItem


class CourseBundleItemInline(admin.TabularInline):
    model = CourseBundleItem
    fields = ["course", "course_series", "position_in_course_bundle"]
    extra = 0
    show_change_link = True
    autocomplete_fields = [
        "course",
        "course_series",
    ]

    def get_formset(self, request, obj=None, **kwargs):  # type: ignore
        formset = super().get_formset(request, obj, **kwargs)

        course_field = formset.form.base_fields["course"]
        course_field.widget.can_delete_related = False
        course_field.widget.can_change_related = False
        course_field.widget.can_add_related = False

        course_series_field = formset.form.base_fields["course_series"]
        course_series_field.widget.can_delete_related = False
        course_series_field.widget.can_change_related = False
        course_series_field.widget.can_add_related = False

        return formset


@admin.register(CourseBundleContent)
class CourseBundleContentAdmin(admin.ModelAdmin):
    fields = ["name", "slug", "orientation", "position_on_page", "is_hidden", "badge_text", "badge_icon", "badge_color", "personalization_categories"]
    list_display = ["name", "slug", "orientation", "position_on_page", "is_hidden"]

    prepopulated_fields = {
        "slug": ["name"],
    }
    search_fields = ["name", "slug"]

    inlines = [CourseBundleItemInline]

    filter_horizontal = ("personalization_categories",)

    def get_inlines(self, request, obj=None):  # type: ignore
        if obj:
            return self.inlines
        return []
