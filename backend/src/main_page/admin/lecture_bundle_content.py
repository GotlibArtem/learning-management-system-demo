from django.contrib import admin

from main_page.models import LectureBundleContent, LectureBundleItem


class LectureBundleItemInline(admin.TabularInline):
    model = LectureBundleItem
    fields = ["lecture", "position_in_lecture_bundle"]
    extra = 0
    show_change_link = True
    autocomplete_fields = ["lecture"]

    def get_formset(self, request, obj=None, **kwargs):  # type: ignore
        formset = super().get_formset(request, obj, **kwargs)

        lecture_field = formset.form.base_fields["lecture"]
        lecture_field.widget.can_delete_related = False
        lecture_field.widget.can_change_related = False
        lecture_field.widget.can_add_related = False

        return formset


@admin.register(LectureBundleContent)
class LectureBundleContentAdmin(admin.ModelAdmin):
    fields = ["name", "slug", "position_on_page", "is_hidden", "badge_text", "badge_icon", "badge_color", "personalization_categories"]
    list_display = ["name", "slug", "position_on_page", "is_hidden"]

    prepopulated_fields = {
        "slug": ["name"],
    }
    search_fields = ["name", "slug"]

    inlines = [LectureBundleItemInline]

    filter_horizontal = ("personalization_categories",)

    def get_inlines(self, request, obj=None):  # type: ignore
        if obj:
            return self.inlines
        return []
