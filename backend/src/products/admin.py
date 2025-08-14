from typing import Any

from django import forms
from django.contrib.admin import TabularInline, register
from django.core.exceptions import ValidationError
from django.db.transaction import on_commit
from django.http import HttpRequest

from app.admin import ModelAdmin
from products.models import CourseVersionPlanProduct, Product
from products.services import ProductTypeValidatorException, product_type_validator


course_versions_plans_inline = "course_version_plans-{num}-{field}"


class ProductForm(forms.ModelForm):
    def clean(self) -> dict[str, Any] | None:
        super().clean()
        self.cleaned_data["course_versions_plans"] = self.get_course_versions_plans_data()
        try:
            product_type_validator.validate(
                product_type=self.cleaned_data.get("product_type", ""),
                course_versions_plans=self.cleaned_data["course_versions_plans"],
                course_series=self.cleaned_data["course_series"],
            )
        except ProductTypeValidatorException as e:
            raise ValidationError(str(e))

        apple_product_id = self.cleaned_data.get("apple_product_id")
        lifetime = self.cleaned_data.get("lifetime")
        if apple_product_id and not lifetime:
            raise ValidationError(
                {
                    "lifetime": "Lifetime is required if Apple Product ID is set.",
                },
            )

        return self.cleaned_data

    def get_course_versions_plans_data(self) -> list[dict]:
        """Hack to get course_versions_plans data from the form data, coz it's placed in the inline formset"""
        plans_count = self.data.get("course_version_plans-TOTAL_FORMS", 0)
        plans_data = []
        for plan_num in range(int(plans_count)):
            try:
                if self.data.get(course_versions_plans_inline.format(num=plan_num, field="DELETE")) == "on":
                    continue
                plan_data = {
                    "course_version": self.data[course_versions_plans_inline.format(num=plan_num, field="course_version")],
                    "course_plan": self.data[course_versions_plans_inline.format(num=plan_num, field="course_plan")],
                }
                plans_data.append(plan_data)
            except ValueError:
                pass
        return plans_data


class CourseVersionPlanProductInline(TabularInline):
    model = CourseVersionPlanProduct
    extra = 0
    fields = [
        "course_version",
        "course_plan",
    ]
    autocomplete_fields = [
        "course_version",
        "course_plan",
    ]


@register(Product)
class ProductAdmin(ModelAdmin):
    list_display = [
        "name",
        "created",
        "id",
        "shop_id",
        "apple_product_id",
    ]
    fields = [
        "name",
        "product_type",
        "course_series",
        "shop_id",
        "apple_product_id",
        "lifetime",
        "redirect_url",
    ]
    readonly_fields = [
        "shop_id",
    ]
    search_fields = [
        "name",
        "=id",
        "=shop_id",
        "=apple_product_id",
    ]
    autocomplete_fields = [
        "course_series",
    ]
    form = ProductForm
    inlines = [CourseVersionPlanProductInline]
