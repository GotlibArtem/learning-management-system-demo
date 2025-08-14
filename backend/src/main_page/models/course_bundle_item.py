from typing import Self

from django.apps import apps
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel, models
from users.models import User


class CourseBundleItemQuerySet(models.QuerySet):
    def for_viewset(self, user: User) -> Self:
        Course = apps.get_model("courses", "Course")
        CourseSeries = apps.get_model("courses", "CourseSeries")
        courses_with_aggregations = models.Prefetch(
            "course",
            queryset=Course.objects.for_catalog_preview(user).select_related("category"),
        )
        series_prefetch = models.Prefetch(
            "course_series",
            queryset=CourseSeries.objects.for_catalog_preview(user).with_published_course_versions(),
        )
        return self.published().prefetch_related(series_prefetch).prefetch_related(courses_with_aggregations).order_by("position_in_course_bundle")

    def published(self) -> Self:
        return self.filter(models.Q(course__course_versions__state="published") | models.Q(course_series__state="published")).distinct()


class CourseBundleItem(TimestampedModel):
    objects = CourseBundleItemQuerySet.as_manager()

    bundle = models.ForeignKey("main_page.CourseBundleContent", on_delete=models.CASCADE, verbose_name=_("Course bundle"), related_name="items")
    course = models.ForeignKey(
        "courses.Course",
        verbose_name=_("Course"),
        on_delete=models.PROTECT,
        related_name="lecture_bundle_items",
        null=True,
        blank=True,
    )
    course_series = models.ForeignKey(
        "courses.CourseSeries",
        verbose_name=_("Course series"),
        on_delete=models.PROTECT,
        related_name="lecture_bundle_items",
        null=True,
        blank=True,
    )

    position_in_course_bundle = models.PositiveSmallIntegerField(verbose_name=_("Position in course bundle"), default=1, db_index=True)

    class Meta:
        verbose_name = _("Course bundle item")
        verbose_name_plural = _("Course bundle items")
        ordering = ["position_in_course_bundle"]
        constraints = [
            models.CheckConstraint(
                check=(models.Q(course=None) ^ models.Q(course_series=None)),
                name="course_or_course_series_specified",
            ),
            models.UniqueConstraint(fields=["bundle", "course"], name="unique_course_per_bundle"),
            models.UniqueConstraint(fields=["bundle", "course_series"], name="unique_course_series_per_bundle"),
        ]
