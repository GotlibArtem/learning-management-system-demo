from courses.api.demo.serializers import (
    CatalogCourseSerializer,
    CatalogCourseSeriesSerializer,
    CategorySerializer,
    CourseSimpleSerializer,
)
from courses.api.demo.serializers.general import BlockFromPublishedLectureBlockField
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from lecturers.api.demo.serializers import LecturerSimpleSerializer
from progress.api.demo.serializers import LectureProgressSimpleSerializer
from rest_framework import serializers
from rest_framework.utils.serializer_helpers import ReturnDict

from main_page.models import (
    CourseBundleContent,
    LectureBundleContent,
    LectureBundleItem,
    LecturersContent,
    MainPageContent,
)
from main_page.models.main_page_content import (
    CATEGORIES_CONTENT_REF,
    COURSE_BUNDLE_CONTENT_REF,
    LECTURE_BUNDLE_CONTENT_REF,
    LECTURERS_CONTENT_REF,
)


class LecturersContentSerializer(serializers.ModelSerializer):
    lecturers = serializers.SerializerMethodField()

    class Meta:
        model = LecturersContent
        fields = ["name", "lecturers"]
        read_only_fields = fields

    @extend_schema_field(LecturerSimpleSerializer(many=True, read_only=True))
    def get_lecturers(self, instance: MainPageContent) -> list:
        return LecturerSimpleSerializer(self.context["lecturers_qs"], many=True).data  # type: ignore


class CategoriesContentSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()

    class Meta:
        model = LecturersContent
        fields = ["name", "categories"]
        read_only_fields = fields

    @extend_schema_field(CategorySerializer(many=True, read_only=True))
    def get_categories(self, instance: MainPageContent) -> list:
        return CategorySerializer(self.context["categories_qs"], many=True).data  # type: ignore


class LectureBundleContentSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LectureBundleContent
        fields = ["name", "slug", "badge_text", "badge_icon", "badge_color"]
        read_only_fields = fields


class CourseBundleContentSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseBundleContent
        fields = [
            "name",
            "slug",
            "orientation",
            "badge_text",
            "badge_icon",
            "badge_color",
        ]
        read_only_fields = fields


main_page_content_serializers_map = {
    LECTURERS_CONTENT_REF: LecturersContentSerializer,
    CATEGORIES_CONTENT_REF: CategoriesContentSerializer,
    LECTURE_BUNDLE_CONTENT_REF: LectureBundleContentSimpleSerializer,
    COURSE_BUNDLE_CONTENT_REF: CourseBundleContentSimpleSerializer,
}


pretty_main_page_content_type_map = {
    LECTURERS_CONTENT_REF: "lecturers-content",
    CATEGORIES_CONTENT_REF: "categories-content",
    LECTURE_BUNDLE_CONTENT_REF: "lecture-bundle-content",
    COURSE_BUNDLE_CONTENT_REF: "course-bundle-content",
}


class MainPageContentSerializer(serializers.ModelSerializer):
    main_page_content_type = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    class Meta:
        model = MainPageContent
        fields = [
            "id",
            "main_page_content_type",
            "content",
        ]
        read_only_fields = fields

    @extend_schema_field(
        field=PolymorphicProxySerializer(
            component_name="MetaMainPageContent",
            serializers=list(main_page_content_serializers_map.values()),
            resource_type_field_name=None,
        ),
    )
    def get_content(self, instance: MainPageContent) -> dict:
        content_type = instance.subclass_instance.main_page_content_type
        return main_page_content_serializers_map[content_type](
            instance=instance.subclass_instance,
            context=self.context,
        ).data

    @extend_schema_field(
        serializers.ChoiceField(
            choices=list(pretty_main_page_content_type_map.values()),
        ),
    )
    def get_main_page_content_type(self, instance: MainPageContent) -> str:
        return pretty_main_page_content_type_map[instance.main_page_content_type]


class LectureForBundleSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="lecture.name")
    slug = serializers.CharField(source="lecture.slug")
    content_url = serializers.CharField(source="lecture.content_url")
    scheduled_at = serializers.CharField(source="lecture.scheduled_at")
    is_available = serializers.BooleanField(source="lecture.is_available")
    duration_in_seconds = serializers.IntegerField(
        source="lecture.duration_in_seconds",
        allow_null=True,
    )
    description = serializers.CharField(source="lecture.description")

    course = CourseSimpleSerializer(source="lecture.course_with_fallback")
    progress = LectureProgressSimpleSerializer(source="lecture.user_progress")
    cover_landscape = serializers.ImageField(
        source="lecture.cover_landscape",
        allow_null=True,
    )
    block = BlockFromPublishedLectureBlockField(source="lecture")

    class Meta:
        model = LectureBundleItem
        fields = [
            "block",
            "name",
            "slug",
            "content_url",
            "scheduled_at",
            "course",
            "is_available",
            "duration_in_seconds",
            "progress",
            "description",
            "cover_landscape",
        ]
        read_only_fields = fields


class LectureBundleContentSerializer(serializers.ModelSerializer):
    lectures = LectureForBundleSerializer(many=True, source="items")

    class Meta:
        model = LectureBundleContent
        fields = ["name", "slug", "badge_text", "badge_icon", "badge_color", "lectures"]
        read_only_fields = fields


class CourseBundleContentSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = CourseBundleContent
        fields = [
            "name",
            "slug",
            "orientation",
            "badge_text",
            "badge_icon",
            "badge_color",
            "items",
        ]
        read_only_fields = fields

    @extend_schema_field(
        field=PolymorphicProxySerializer(
            component_name="CourseBundleItem",
            serializers=[CatalogCourseSerializer, CatalogCourseSeriesSerializer],
            resource_type_field_name=None,
            many=True,
        ),
    )
    def get_items(self, instance: CourseBundleContent) -> list[ReturnDict]:
        courses = []
        course_series = []
        sort_weights = {}
        for index, item in enumerate(instance.items.all()):
            if item.course:
                sort_weights[item.course.slug] = index
                courses.append(item.course)
            else:
                sort_weights[item.course_series.slug] = index
                course_series.append(item.course_series)
        serialized_items = [
            *CatalogCourseSerializer(instance=courses, many=True).data,
            *CatalogCourseSeriesSerializer(instance=course_series, many=True).data,
        ]
        return sorted(serialized_items, key=lambda item: sort_weights[item["slug"]])
