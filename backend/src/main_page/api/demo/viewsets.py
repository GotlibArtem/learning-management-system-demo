from typing import Any

from courses.api.demo.serializers import MainPageRecommendationCourseSerializer
from courses.models import Category, Course
from django.conf import settings
from django.db.models import Prefetch, QuerySet
from lecturers.models import Lecturer
from rest_framework.permissions import IsAuthenticated

from app.api.request import AuthenticatedRequest
from app.api.viewsets import ListOnlyModelViewSet, ReadonlyModelViewSet
from app.models import models
from main_page.api.demo.filters import CourseBundleContentFilterSet, LectureBundleContentFilterSet
from main_page.api.demo.serializers import (
    CourseBundleContentSerializer,
    LectureBundleContentSerializer,
    MainPageContentSerializer,
)
from main_page.models import CourseBundleContent, CourseBundleItem, LectureBundleContent, LectureBundleItem, MainPageContent, MainPageRecommendation


class MainPageRecommendationsViewSet(ListOnlyModelViewSet):
    serializer_class = MainPageRecommendationCourseSerializer
    permission_classes = [IsAuthenticated]
    queryset = Course.objects.all()
    pagination_class = None

    def get_queryset(self) -> QuerySet[Course]:
        recommendation_courses_ids = MainPageRecommendation.objects.values_list("course_id", flat=True)
        return super().get_queryset().filter(pk__in=recommendation_courses_ids).for_main_page_recommendations(self.request.user)  # type: ignore


class MainPageContentViewSet(ListOnlyModelViewSet):
    serializer_class = MainPageContentSerializer
    permission_classes = [IsAuthenticated]
    queryset = MainPageContent.objects.for_viewset()

    request: AuthenticatedRequest

    def get_queryset(self) -> QuerySet[MainPageContent]:
        qs = super().get_queryset()

        if self.request.user.interests.exists() and not self.request.user.all_interests:
            qs = qs.with_personalization(self.request.user).order_by(  # type: ignore[attr-defined]
                models.F("is_personalized").desc(nulls_last=True),
                "position_on_page",
                "created",
            )
        return qs

    def get_serializer_context(self) -> dict[str, Any]:
        context = super().get_serializer_context()

        # May be it would be better to move this shit to model properties with serializer refactoring
        context["lecturers_qs"] = Lecturer.objects.for_viewset().visible_on_main_page()[: settings.MAX_LECTURERS_ON_MAIN_PAGE]
        context["categories_qs"] = Category.objects.for_viewset().all()

        return context


class LectureBundleContentViewSet(ReadonlyModelViewSet):
    serializer_class = LectureBundleContentSerializer
    permission_classes = [IsAuthenticated]
    queryset = LectureBundleContent.objects.active()
    filterset_class = LectureBundleContentFilterSet
    lookup_field = "slug"

    request: AuthenticatedRequest

    def get_queryset(self) -> QuerySet[LectureBundleContent]:
        return super().get_queryset().prefetch_related(Prefetch("items", queryset=LectureBundleItem.objects.for_viewset(self.request.user)))


class CourseBundleContentViewSet(ReadonlyModelViewSet):
    serializer_class = CourseBundleContentSerializer
    permission_classes = [IsAuthenticated]
    queryset = CourseBundleContent.objects.active()
    filterset_class = CourseBundleContentFilterSet
    lookup_field = "slug"

    request: AuthenticatedRequest

    def get_queryset(self) -> QuerySet[CourseBundleContent]:
        return super().get_queryset().prefetch_related(Prefetch("items", queryset=CourseBundleItem.objects.for_viewset(self.request.user)))
