from django_filters import rest_framework as filters

from app.api.filters import StringInFilter
from main_page.models import CourseBundleContent, LectureBundleContent


class LectureBundleContentFilterSet(filters.FilterSet):
    slugs = StringInFilter(field_name="slug")

    class Meta:
        model = LectureBundleContent
        fields = ["slugs"]


class CourseBundleContentFilterSet(filters.FilterSet):
    slugs = StringInFilter(field_name="slug")

    class Meta:
        model = CourseBundleContent
        fields = ["slugs"]
