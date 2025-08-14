from django.contrib import admin

from main_page.models import CategoriesContent, CourseBundleContent, LectureBundleContent, LecturersContent, MainPageContent
from main_page.models.main_page_content import CATEGORIES_CONTENT_REF, COURSE_BUNDLE_CONTENT_REF, LECTURE_BUNDLE_CONTENT_REF, LECTURERS_CONTENT_REF


class SubclassContentMixin:
    fields = ["name"]
    readonly_fields = ["name"]
    extra = 0
    show_change_link = True

    def has_add_permission(self, request, obj) -> bool:  # type: ignore
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # type: ignore
        return False

    def has_delete_permission(self, request, obj=None) -> bool:  # type: ignore
        return False


class LecturersContentInline(SubclassContentMixin, admin.TabularInline):  # type: ignore
    model = LecturersContent


class CategoriesContentInline(SubclassContentMixin, admin.TabularInline):  # type: ignore
    model = CategoriesContent


class LectureBundleContentInline(SubclassContentMixin, admin.TabularInline):  # type: ignore
    model = LectureBundleContent


class CourseBundleContentInline(SubclassContentMixin, admin.TabularInline):  # type: ignore
    model = CourseBundleContent


@admin.register(MainPageContent)
class MainPageContentAdmin(admin.ModelAdmin):
    fields = ["name", "main_page_content_type", "position_on_page", "is_hidden"]
    list_display = ["name", "main_page_content_type", "position_on_page", "is_hidden"]
    list_editable = ["position_on_page", "is_hidden"]
    readonly_fields = ["main_page_content_type"]

    inlines = ()

    def has_add_permission(self, request) -> bool:  # type: ignore
        return False

    def get_inlines(self, request, obj=None):  # type: ignore
        if not obj:
            return self.inlines

        return {
            LECTURERS_CONTENT_REF: [LecturersContentInline],
            CATEGORIES_CONTENT_REF: [CategoriesContentInline],
            LECTURE_BUNDLE_CONTENT_REF: [LectureBundleContentInline],
            COURSE_BUNDLE_CONTENT_REF: [CourseBundleContentInline],
        }.get(obj.main_page_content_type, [])


@admin.register(LecturersContent)
class LecturersContentAdmin(admin.ModelAdmin):
    fields = ["name", "position_on_page", "is_hidden"]
    list_display = ["name", "position_on_page", "is_hidden"]


@admin.register(CategoriesContent)
class CategoriesContentAdmin(admin.ModelAdmin):
    fields = ["name", "position_on_page", "is_hidden"]
    list_display = ["name", "position_on_page", "is_hidden"]
